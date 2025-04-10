import logging
import pandas as pd
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from team_formation.team_assignment import TeamAssignment

def diversify_model():
    participants = pd.DataFrame(
        columns=[
            "id",
            "gender",
        ],
        data=[[8, "Female"],
              [9, "Female"],
              [10, "Male"],
              [16, "Female"],
              [18, "Male"],
              [20, "Male"],
              [21, "Female"],
              [29, "Male"],
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
    

def test_diversify():
    ta = diversify_model()
    print(ta.participants)

    # Check matching number of participants
    assert(ta.num_participants == len(ta.participants))
    # No solution should be found yet
    assert (not ta.solution_found), "Solution should not be found"
    
    ta.solve(log_progress=True)

    # Solution should be found
    assert ta.solution_found, "No solution found"
    # Resulting teams should all be of size 3
    assert (all(ta.participants["team_num"].value_counts() == 3)), "Wrong team sizes"
