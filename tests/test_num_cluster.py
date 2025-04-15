import logging
import pandas as pd
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from team_formation.team_assignment import TeamAssignment

def small_model():
    participants = pd.DataFrame(
        columns=[
            "id",
            "years_experience",
        ],
        data=[[8, 1],
              [9, 10],
              [10, 8],
              [16, 2],
              [18, 5],
              [20, 6],
              [21, 1],
              [29, 5],
              [31, 10]],
    )
    target_team_size = 3
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[
            ["years_experience", "cluster_numeric", 1],
        ],
    )
    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size,
    )
    return ta
    

def test_num_cluster():
    ta = small_model()
    print(ta.participants)

    # Check matching number of participants
    assert(ta.num_participants == len(ta.participants))
    # No solution should be found yet
    assert(not ta.solution_found)
    
    ta.solve()

    # Solution should be found
    assert(ta.solution_found)
    # Resulting teams should all be of size 3
    assert(all(ta.participants["team_num"].value_counts() == 3))
    
