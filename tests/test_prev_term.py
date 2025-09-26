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
TEST_ROSTER = os.path.join(TEST_DIR, "data", "roster_prev_term_test.csv")

def roster_model():
    partis = (
        pd.read_csv(TEST_ROSTER)
        .assign(working_hour_list = lambda x: x["working_hour_list"].str.split(";"))
    )
    constraints = pd.DataFrame({
        "attribute": [
            "gender",
            "working_hour_list",
            "term_2_team_num",
            "term_1_team_num",
        ],
        "type": ["diversify", "cluster", "different", "different"],
        "weight": [3, 4, 2, 1],
    })
    target_team_size = 7
    ta = TeamAssignment(
        partis,
        constraints,
        target_team_size,
        less_than_target=True,
    )
    return ta

def team_costs(ta):
    team_costs = [
        sum([ta.solver.Value(cost_var) for cost_var
             in ta.attr_costs
             if f"_cost_{team_num}_" in cost_var.name])
        for team_num in range(ta.num_teams)
    ]
    return team_costs

def test_prev_term():
    ta = roster_model()
    ta.solve(solution_callback=SolutionCallback(stop_after_seconds=5))
    print(ta.participants.sort_values("team_num").to_string())

def main():
    test_prev_term()
    
if __name__ == "__main__":
    main()
