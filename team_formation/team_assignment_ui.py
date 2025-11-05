import streamlit as st
import pandas as pd
import datetime
from threading import Thread, Event
import time
import threading

import team_formation
from team_assignment import TeamAssignment, SolutionCallback
from team_formation.working_time import working_times_hours
from ortools.sat.python import cp_model

# Handle working time in the roster download
ENABLE_WORKING_TIME = False

def roster_upload_callback():
    roster_upload = st.session_state["roster_upload"]
    if roster_upload.type == "text/csv":
         roster = (pd.read_csv(roster_upload)
                   .pipe(create_list_columns))
    elif roster_upload.type == "application/json":
        roster = pd.read_json(roster_upload)
    st.session_state["roster"] = roster

def create_list_columns(df):
    new_df = df.copy()
    for list_col in (col for col in df.columns
                     if col.endswith("_list")):
        new_df[list_col] = split_list_column(new_df[list_col])
    return new_df

def split_list_column(series):
    new_series = series.map(lambda str_val: str_val.split(";"))
    return new_series

def constraints_are_valid():
    valid = True
    constraints = st.session_state["constraints"]
    constraint_columns = constraints.columns
    required_columns = ["attribute", "type", "weight"]
    for req_col in required_columns:
        if req_col not in constraint_columns:
            st.error(f"Constraints missing required column: '{req_col}'")
            valid = False
    if "roster" in st.session_state:
        roster = st.session_state["roster"]
        attributes = list(constraints["attribute"])
        roster_columns = list(roster.columns)
        for attribute in attributes:
            if attribute not in roster_columns:
                st.error(f"Constraint does not exist as roster column: '{attribute}'")
                valid = False
    return valid

def constraints_upload_callback():
    constraints_upload = st.session_state["constraints_upload"]
    if constraints_upload.type == "text/csv":
         constraints = pd.read_csv(constraints_upload)
    elif constraints_upload.type == "application/json":
        constraints = pd.read_json(constraints_upload)
    st.session_state["constraints"] = constraints
    constraints_are_valid()

def update_constraints_callback():
    """Update the constraints in the session state when edited in the UI"""
    if "edited_constraints" in st.session_state:
        st.session_state["constraints"] = st.session_state["edited_constraints"]

class ProgressTracker:
    """Thread-safe progress tracker for sharing data between solver and UI."""

    def __init__(self):
        self.lock = threading.Lock()
        self.solution_count = 0
        self.best_objective = float('inf')
        self.wall_time = 0.0
        self.num_conflicts = 0
        self.is_running = False
        self.is_complete = False
        self.success = False

    def update(self, solution_count, objective_value, wall_time, num_conflicts):
        """Update progress data in a thread-safe manner."""
        with self.lock:
            self.solution_count = solution_count
            if objective_value < self.best_objective:
                self.best_objective = objective_value
            self.wall_time = wall_time
            self.num_conflicts = num_conflicts

    def get_status(self):
        """Get current status in a thread-safe manner."""
        with self.lock:
            return {
                'solution_count': self.solution_count,
                'best_objective': self.best_objective,
                'wall_time': self.wall_time,
                'num_conflicts': self.num_conflicts,
                'is_running': self.is_running,
                'is_complete': self.is_complete,
                'success': self.success
            }

    def set_running(self, running):
        with self.lock:
            self.is_running = running

    def set_complete(self, success):
        with self.lock:
            self.is_complete = True
            self.is_running = False
            self.success = success


class StreamlitSolutionCallback(SolutionCallback):
    """Solution callback that tracks progress without directly updating UI."""

    def __init__(self, progress_tracker, stop_after_seconds=None):
        super().__init__(stop_after_seconds=stop_after_seconds)
        self.progress_tracker = progress_tracker
        self.solution_count = 0

    def on_solution_callback(self):
        # Call parent implementation for stdout logging and stop logic
        super().on_solution_callback()

        # Update progress tracker (thread-safe)
        self.solution_count += 1
        self.progress_tracker.update(
            self.solution_count,
            self.objective_value,
            self.wall_time,
            self.num_conflicts
        )

def solver_worker(ta, callback, progress_tracker, max_time):
    """Run the solver in a separate thread."""
    progress_tracker.set_running(True)
    try:
        ta.solve(
            solution_callback=callback,
            max_time_in_seconds=max_time,
        )
        progress_tracker.set_complete(ta.solution_found)
    except Exception as e:
        progress_tracker.set_complete(False)
        raise e
        
def generate_teams_callback():
    if not constraints_are_valid():
        return
    less_than_target = (st.session_state["over_under_size"] == "Under")
    print("Generating teams with constraints:")
    print(st.session_state["constraints"])
    team_assignment = TeamAssignment(
        st.session_state["roster"],
        st.session_state["constraints"],
        st.session_state["target_team_size"],
        less_than_target=less_than_target,
    )
    st.session_state["team_assignment"] = team_assignment
    stop_after_seconds = st.session_state["stop_after_seconds"]

    # Create progress tracker and callback
    progress_tracker = ProgressTracker()
    callback = StreamlitSolutionCallback(
        progress_tracker=progress_tracker,
    )

    # Create containers for progress updates
    progress_container = st.empty()
    status_container = st.empty()

    # Start solver in background thread
    solver_thread = Thread(
        target=solver_worker,
        args=(team_assignment, callback, progress_tracker, stop_after_seconds)
    )
    solver_thread.start()

    # Poll for progress updates
    with progress_container:
        st.progress(0.0, text="Starting search...")

    # Update loop
    while True:
        status = progress_tracker.get_status()

        if status['is_complete']:
            break

        if status['is_running']:
            # Update progress display
            with status_container:
                st.markdown(f"""
                **Search Progress:**
                - Solutions found: {status['solution_count']}
                - Best objective: {status['best_objective']}
                - Elapsed time: {status['wall_time']:.1f}s
                - Conflicts: {status['num_conflicts']}
                """)

            # Update progress bar
            if stop_after_seconds and status['wall_time'] > 0:
                time_progress = min(status['wall_time'] / stop_after_seconds, 1.0)
                with progress_container:
                    st.progress(
                        time_progress,
                        text=f"Searching... ({status['wall_time']:.1f}s / {stop_after_seconds}s)"
                    )

        # Sleep briefly to avoid busy waiting
        time.sleep(0.5)

    # Wait for thread to complete
    solver_thread.join()

    # Handle completion
    final_status = progress_tracker.get_status()
    if final_status['success']:
        st.session_state["solution_found"] = True
        roster_teams = (team_assignment
                        .participants
                        .sort_values("team_num"))
        st.session_state["roster"] = roster_teams
        roster_csv = roster_teams.to_csv(index=False).encode("utf-8")
        st.session_state["roster_csv"] = roster_csv
        st.session_state["team_eval"] = team_assignment.evaluate_teams()

        # Clear progress containers and show completion
        progress_container.empty()
        status_container.success("✅ Team generation completed successfully!")
    else:
        # Clear progress containers and show failure
        progress_container.empty()
        status_container.error("❌ No feasible solution found. Try adjusting constraints or time limit.")
    
def translate_working_time():
    roster = st.session_state["roster"]
    ref_date = st.session_state["reference_date"]
    time_zone_column = st.session_state["time_zone_column"]
    preferred_time_column = st.session_state["preferred_time_column"]
    roster["working_hour_list"] = working_times_hours(
        roster,
        ref_date,
        time_zone_column,
        preferred_time_column,
    )
    roster["working_hour_list"] = split_list_column(roster["working_hour_list"])
    st.session_state["roster"] = roster

st.set_page_config(
    layout="wide",
    page_title="Constraint-Based Team Formation",
    menu_items={
        "About": f"# team-formation v{team_formation.__version__}",
    },
)
st.title("Team Formation")

st.markdown("""
This application is designed to divide a group of
individuals into a set of smaller teams at or close to a particular target
team size. The assignment is guided by a sert of constraints on the individual's
attributes that either prefer attribute similarity (clustering) or attribute
difference (diversification).

The process for creating teams:
1. Upload the roster of individuals containing your attributes.
2. Optional: Convert time zone and preferred time columns into
   available hours (Working Time Hours).
3. Upload and edit the constraints.
4. Set the desired team size, whether to round to over or under target size, and maximum search time.
4. Generate the teams.
5. Download the roster with associated teams.
""")

st.subheader("Roster")

if "roster" in st.session_state:
    roster = st.session_state["roster"]
    st.dataframe(roster)
else:
    st.write("*Roster will appear hear after uploading*")

if "solution_found" in st.session_state:
    st.download_button(label="Download roster teams",
                       data=st.session_state["roster_csv"],
                       file_name="roster_team_assignments.csv",
                       mime="text/csv")

if "team_eval" in st.session_state:
    st.subheader("Team Metrics")
    st.markdown(
        """The team evaluations have a column for each
constrainted attribute and an integer with the following
interpretation:
        
- "cluster" - the number of team members that don't share a discrete attribute.
- "diversify" - the number of team members off from population distribution.
- "cluster_numeric" - the numeric range/spread of the team member's values.
- "different" - the number of team members that share attribute values.
    """
    )
    team_col_1, team_col_2 = st.columns([1, 1])
    with team_col_1:
        team_eval = st.session_state["team_eval"]
        st.dataframe(
            team_eval,
            hide_index=True,
        )
        st.dataframe(
            (team_eval.drop(columns=["team_num", "team_size"]).mean().to_frame(name="mean"))
        )
    
st.subheader("Constraints")
    
if "constraints" in st.session_state:
    const_col_1, const_col_2 = st.columns([1, 1])
    with const_col_1:
        # Create an editable data frame and store the edited version back
        edited_constraints = st.data_editor(
            st.session_state["constraints"],
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "attribute": st.column_config.TextColumn(
                    "Attribute",
                    required=True,
                ),
                "constraint_type": st.column_config.SelectboxColumn(
                    "Constraint Type",
                    required=True,
                    options=TeamAssignment.CONSTRAINT_TYPES,
                ),
                "weight": st.column_config.NumberColumn(
                    "Weight",
                    required=True,
                    min_value=0,
                    max_value=100,
                )
            },
            key="constraints_editor"
        )
        # Update the constraints in session state with the edited version
        st.session_state["constraints"] = edited_constraints
else:
    st.write("*Constraints will appear here after upload*")

if (("target_team_size" in st.session_state) and
    ("over_under_size" in st.session_state) and
    ("roster" in st.session_state) and
    ("constraints" in st.session_state)):
    st.button("Generate teams",
              on_click=generate_teams_callback)
    
st.subheader("Data Upload and Setup")

setup_1, setup_2, setup_3 = st.columns([1, 2, 1])

with setup_1:
    st.number_input("Target team size",
                    min_value=2,
                    value=7,
                    key="target_team_size")
    st.selectbox("Should team sizes round to over or under the target size",
                 options=["Over", "Under"],
                 index=1,
                 key="over_under_size")
    st.number_input("Maximum search time in seconds",
                    value=60,
                    min_value=1,
                    key="stop_after_seconds")

with setup_2:    
    st.file_uploader("Participant roster",
                     type=["csv", "json"],
                     key="roster_upload",
                     on_change=roster_upload_callback)
    st.file_uploader("Assignment constraints",
                     type=["csv", "json"],
                     key="constraints_upload",
                     on_change=constraints_upload_callback)

if ENABLE_WORKING_TIME:    
    st.subheader("Working Time Hours")

    st.markdown(""" The working hour calculation looks for time zone and
    preferred time columns with names specified below and produces a
    new column called `working_hour_list` that can be used in a clustering
    constraint to ensure overlaps in working time.  """)

    working_1, working_2 = st.columns([1, 4])

    with working_1:
        st.date_input(
            "Working hour reference date (usually term start date)",
            key="reference_date",
        )
        st.text_input(
            "Time Zone column name",
            value="time_zone",
            key="time_zone_column",
        )
        st.text_input(
            "Preferred working times column",
            value="preferred_time",
            key="preferred_time_column",
        )

    if ("roster" in st.session_state):
        st.button("Translate working time",
                  on_click=translate_working_time)

