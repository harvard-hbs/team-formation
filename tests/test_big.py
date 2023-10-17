import os
import pandas as pd

from team_formation.team_assignment import TeamAssignment

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BIG_TEST_ROSTER = os.path.join(TEST_DIR, "data", "big_test_roster.json")

def test_big():
    participants = pd.read_json(BIG_TEST_ROSTER)
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[["gender", "diversify", 1],
              ["working_time", "cluster", 1]]
    )
    target_team_size = 10
    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size)
    ta.solve()
    print(ta.participants.sort_values("team_num").to_string())
    team_eval = ta.evaluate_teams()
    print(team_eval.to_string())
