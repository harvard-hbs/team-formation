import streamlit as st
import pandas as pd
import datetime
import humanize

from team_assignment import TeamAssignment
from team_formation.working_time import working_times_hours
from ortools.sat.python import cp_model

class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.start_time = datetime.datetime.now()

    def on_solution_callback(self):
        objective_value = self.ObjectiveValue()
        num_conflicts = self.NumConflicts()
        cur_time = datetime.datetime.now()
        time_diff = cur_time - self.start_time
        time_diff_human = humanize.naturaldelta(time_diff)
        print(
            f"Elapsed time: {time_diff}, Number of conflicts: " +
            f"{num_conflicts}, Objective value: {objective_value}"
        )
        if time_diff.seconds > 10:
            self.StopSearch()

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

def solve_assignment():
    st.session_state["team_assignment"].solve(SolutionCallback())

def generate_teams_callback():
    team_assignment = TeamAssignment(
        st.session_state["roster"],
        st.session_state["constraints"],
        st.session_state["target_team_size"])
    st.session_state["team_assignment"] = team_assignment
    callback = SolutionCallback()
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

def translate_working_time():
    roster = st.session_state["roster"]
    ref_date = st.session_state["reference_date"]
    roster["working_hour_list"] = working_times_hours(roster, ref_date)
    roster["working_hour_list"] = split_list_column(roster["working_hour_list"])
    st.session_state["roster"] = roster
            
st.title("Team Formation")

st.subheader("Roster")

if "roster" in st.session_state:
    roster = st.session_state["roster"]
    st.dataframe(roster, hide_index=True)
else:
    st.write("*Please upload participant roster*")

if "solution_found" in st.session_state:
    st.download_button(label="Download roster teams",
                       data=st.session_state["roster_csv"],
                       file_name="roster_team_assignments.csv",
                       mime="text/csv")

st.subheader("Constraints")
    
if "constraints" in st.session_state:
    constraints = st.session_state["constraints"]
    st.dataframe(constraints, hide_index=True)
else:
    st.write("*Please upload team assignment constraints*")

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
                
st.selectbox("Team sizes over/under",
             options=["Over", "Under"],
             key="over_under_size")
                
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

