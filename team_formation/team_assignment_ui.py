import streamlit as st
import pandas as pd
import datetime
import humanize

from team_assignment import TeamAssignment, SolutionCallback
from team_formation.working_time import working_times_hours
from ortools.sat.python import cp_model

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
    
def constraints_upload_callback():
    constraints_upload = st.session_state["constraints_upload"]
    if constraints_upload.type == "text/csv":
         constraints = pd.read_csv(constraints_upload)
    elif constraints_upload.type == "application/json":
        constraints = pd.read_json(constraints_upload)
    st.session_state["constraints"] = constraints

def update_constraints_callback():
    """Update the constraints in the session state when edited in the UI"""
    if "edited_constraints" in st.session_state:
        st.session_state["constraints"] = st.session_state["edited_constraints"]

def generate_teams_callback():
    less_than_target = (st.session_state["over_under_size"] == "Under")
    team_assignment = TeamAssignment(
        st.session_state["roster"],
        st.session_state["constraints"],
        st.session_state["target_team_size"],
        less_than_target=less_than_target,
    )
    st.session_state["team_assignment"] = team_assignment
    stop_after_seconds = st.session_state["stop_after_seconds"]
    callback = SolutionCallback(stop_after_seconds=stop_after_seconds)
    with st.spinner("Generating teams..."):
        team_assignment.solve(solution_callback=callback)
        if team_assignment.solution_found:
            st.session_state["solution_found"] = True
            roster_teams = (team_assignment
                            .participants
                            .sort_values("team_num"))
            st.session_state["roster"] = roster_teams
            roster_csv = roster_teams.to_csv(index=False).encode("utf-8")
            st.session_state["roster_csv"] = roster_csv
            st.session_state["team_eval"] = team_assignment.evaluate_teams()

def translate_working_time():
    roster = st.session_state["roster"]
    ref_date = st.session_state["reference_date"]
    roster["working_hour_list"] = working_times_hours(roster, ref_date)
    roster["working_hour_list"] = split_list_column(roster["working_hour_list"])
    st.session_state["roster"] = roster
            
st.title("Team Formation")

st.markdown("""
This application is designed to divide a group of
individuals into a set of smaller teams at or close to a particular target
team size. The assignment is guided by a sert of constraints on the individual's
attributes that either prefer attribute similarity (clustering) or attribute
difference (diversification).

The process for creating teams:
1. Upload the roster of individuals containing your attributes.
2. Optional: Convert `time_zone` and `working_time` columns into
   available hours (Working Time Hours).
3. Upload and edit the constraints.
4. Set the desired team size, whether to round to over or under target size, and maximum search time.
4. Generate the teams.
5. Download the roster with associated teams.
""")

st.subheader("Roster")

if "roster" in st.session_state:
    roster = st.session_state["roster"]
    st.dataframe(roster, hide_index=True)
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
    st.dataframe(
        st.session_state["team_eval"],
        hide_index=True,
    )
    
st.subheader("Constraints")
    
if "constraints" in st.session_state:
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

st.number_input("Target team size",
                min_value=2,
                key="target_team_size")
                
st.selectbox("Should team sizes round to over or under the target size",
             options=["Over", "Under"],
             key="over_under_size")

st.number_input("Maximum search time in seconds",
                value=60,
                min_value=1,
                key="stop_after_seconds")

st.file_uploader("Participant roster",
                 type=["csv", "json"],
                 key="roster_upload",
                 on_change=roster_upload_callback)

st.file_uploader("Assignment constraints",
                 type=["csv", "json"],
                 key="constraints_upload",
                 on_change=constraints_upload_callback)

st.subheader("Working Time Hours")

st.markdown("""
The working hour calculation expects roster columns of
`time_zone` and `working_time` and produces a new column
called `working_hour_list` that can be used in a clustering
constraint to ensure overlaps in working time.
""")

st.date_input(
    "Working hour reference date (usually term start date)",
    key="reference_date",
)

if ("roster" in st.session_state):
    st.button("Translate working time",
              on_click=translate_working_time)

