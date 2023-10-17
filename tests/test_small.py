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
    # constraints = {
    #     "gender": {"type": "diversify", "weight": 1},
    #     "job_function": {"type": "cluster", "weight": 1},
    #     "working_time": {"type": "cluster", "weight": 1},
    # }
    print(participants)
    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size)
    ta.solve()
    print(ta.participants.sort_values("team_num"))
    team_eval = ta.evaluate_teams()
    print(team_eval)
