import logging
import pandas as pd
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from team_formation.team_assignment import TeamAssignment

def small_model():
    participants = pd.DataFrame(
        columns=[
            "id",
            "gender",
        ],
        data=[[8, "Male"],
              [9, "Male"],
              [10, "Female"],
              [16, "Male"],
              [18, "Female"],
              [20, "Female"],
              [21, "Male"],
              [29, "Female"],
              [31, "Female"]],
    )
    target_team_size = 3
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[
            ["gender", "diversify", 1],
         ],
    )
    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size,
    )
    return ta
    

def test_small():
    ta = small_model()
    print(ta.participants)

    # Check matching number of participants
    assert(ta.num_participants == len(ta.participants))
    # No solution should be found yet
    assert (not ta.solution_found), "Solution should not be found"
    
    ta.solve()

    # Solution should be found
    assert ta.solution_found, "No solution found"
    # Resulting teams should all be of size 3
    assert (all(ta.participants["team_num"].value_counts() == 3)), "Wrong team sizes"
