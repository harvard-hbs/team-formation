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
            "job_function",
            "working_time",
            "years_experience",
        ],
        data=[[8, "Male", "Manager", ["00-05", "20-24"], 10],
              [9, "Male", "Executive", ["10-15", "15-20"], 10],
              [10, "Female", "Executive", ["15-20"], 15],
              [16, "Male", "Manager", ["15-20", "20-24"], 7],
              [18, "Female", "Contributor", ["05-10", "10-15"], 3],
              [20, "Female", "Manager", ["15-20", "20-24"], 5],
              [21, "Male", "Executive", ["15-20"], 13],
              [29, "Male", "Contributor", ["05-10", "10-15"], 4],
              [31, "Female", "Contributor", ["05-10"], 1]]
    )
    target_team_size = 3
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[
            ["gender", "diversify", 1],
            ["job_function", "cluster", 1],
            ["working_time", "cluster", 1],
            ["years_experience", "cluster_numeric", 1],
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
    assert(not ta.solution_found)
    
    ta.solve()

    # Solution should be found
    assert(ta.solution_found)
    # Resulting teams should all be of size 3
    assert(all(ta.participants["team_num"].value_counts() == 3))
    
    print(ta.participants.sort_values("team_num"))
    team_eval = ta.evaluate_teams()

    # There should be only one miss
    assert(sum(team_eval["missed"] > 0) == 1)
    print(team_eval)

def test_micro():
    ta = micro_model()
    ta.solve(log_progress=True)
    assert(ta.solution_found)

def micro_model():
    participants = pd.DataFrame(
        columns=["id", "gender", "age"],
        data=[
            [8, "Male", 43],
            [9, "Female", 58],
            [10, "Male", 56],
            [16, "Female", 47],
        ],
    )
    target_team_size = 2
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[
            ["gender", "diversify", 1],
            ["age", "cluster_numeric", 1],
        ]
    )
    print(participants)
    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size,
    )
    return ta

def main():
    test_small()

if __name__ == "__main__":
    main()
