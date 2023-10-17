import streamlit as st
import pandas as pd
import threading

from team_assignment import TeamAssignment, SolutionCallback

def roster_upload_callback():
    roster_upload = st.session_state["roster_upload"]
    if roster_upload.type == "text/csv":
         roster = pd.read_csv(roster_upload)
    elif roster_upload.type == "application/json":
        roster = pd.read_json(roster_upload)
    st.session_state["roster"] = roster

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
    with st.spinner("Generating teams..."):
        team_assignment.solve()
        if team_assignment.solution_found:
            st.session_state["solution_found"] = True
            roster_teams = (team_assignment
                            .participants
                            .sort_values("team_num"))
            st.session_state["roster"] = roster_teams
            roster_csv = roster_teams.to_csv(index=False).encode("utf-8")
            st.session_state["roster_csv"] = roster_csv

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

