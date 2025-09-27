import datetime
import logging
import os
import pandas as pd
import sys

# logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from ortools.sat.python import cp_model
from team_formation.team_assignment import (
    TeamAssignment,
    SolutionCallback,
)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_ROSTER = os.path.join(TEST_DIR, "data", "test_roster_2.csv")

def roster_model():
    partis = pd.read_csv(TEST_ROSTER)
    constraints = pd.DataFrame({
        "attribute": ["work_experience_years"],
        "type": ["cluster_numeric"],
        "weight": 1,
    })
    target_team_size = 7
    ta = TeamAssignment(
        partis,
        constraints,
        target_team_size,
        less_than_target=True,
    )
    return ta

def test_roster():
    ta = roster_model()
    ta.solve(
        solution_callback=SolutionCallback(),
        max_time_in_seconds=20,
    )
    print(ta.participants.sort_values("team_num").to_string())
    print([ta.solver.Value(var) for var in ta.attr_costs])

def main():
    test_roster()
    
if __name__ == "__main__":
    main()
