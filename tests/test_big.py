import os
import pandas as pd

from team_formation.team_assignment import TeamAssignment

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BIG_TEST_ROSTER = os.path.join(TEST_DIR, "data", "big_test_roster.json")

def test_big():
    participants_all = pd.read_json(BIG_TEST_ROSTER)
    participants = participants_all[214:].copy()
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

    # Check matching number of participants
    assert(ta.num_participants == len(participants))
    # No solution should be found yet
    assert(not ta.solution_found)
    
    ta.solve()

    # Solution should be found
    assert(ta.solution_found)
    # Resulting teams should all be of size 10
    assert(all(ta.participants["team_num"].value_counts() == 10))

    print(ta.participants.sort_values("team_num").to_string())
    team_eval = ta.evaluate_teams()

    # Perfect for working time
    assert (team_eval["working_time"].sum() == 0)
    # No more than two misses for gender
    assert (team_eval["gender"].sum() <= 7)
    print(team_eval.to_string())

    
