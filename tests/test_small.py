import pandas as pd

from team_formation.team_assignment import TeamAssignment

def test_small():
    participants = pd.DataFrame(
        columns=["id", "gender", "job_function", "working_time"],
        data=[[8, "Male", "Manager", ["00-05", "20-24"]],
              [9, "Male", "Executive", ["10-15", "15-20"]],
              [10, "Female", "Executive", ["15-20"]],
              [16, "Male", "Manager", ["15-20", "20-24"]],
              [18, "Female", "Contributor", ["05-10", "10-15"]],
              [20, "Female", "Manager", ["15-20", "20-24"]],
              [21, "Male", "Executive", ["15-20"]],
              [29, "Male", "Contributor", ["05-10", "10-15"]],
              [31, "Female", "Contributor", ["05-10"]]]
    )
    target_team_size = 3
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[["gender", "diversify", 1],
              ["job_function", "cluster", 1],
              ["working_time", "cluster", 1]]
    )
    print(participants)
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
    # Resulting teams should all be of size 3
    assert(all(ta.participants["team_num"].value_counts() == 3))
    
    print(ta.participants.sort_values("team_num"))
    team_eval = ta.evaluate_teams()

    # There should be only one miss
    assert(sum(team_eval["missed"] > 0) == 1)
    print(team_eval)
