import pandas as pd

from team_formation.team_assignment import TeamAssignment

def test_sizel():
    """The purpose of this test is to make sure that the `less_than_target`
    argument is respected."""
    participants = pd.DataFrame(
        columns=["id", "gender", "job_function", "working_time"],
        data=[[8, "Male", "Manager", ["00-05", "20-24"]],
              [9, "Male", "Executive", ["10-15", "15-20"]],
              [10, "Female", "Executive", ["15-20"]],
              [16, "Male", "Manager", ["15-20", "20-24"]],
              [18, "Female", "Contributor", ["05-10", "10-15"]],
              [20, "Female", "Manager", ["15-20", "20-24"]],
              [21, "Male", "Executive", ["15-20"]],
              [31, "Female", "Contributor", ["05-10"]]]
    )
    constraints = pd.DataFrame(
        columns=["attribute", "type", "weight"],
        data=[["gender", "diversify", 1],
              ["job_function", "cluster", 1],
              ["working_time", "cluster", 1]]
    )

    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size = 3,
        less_than_target = True,
    )
    ta.solve()
    # Resulting teams should all be of size 3 or less
    assert(all(ta.participants["team_num"].value_counts() <= 3))

    ta = TeamAssignment(
        participants,
        constraints,
        target_team_size = 3,
        less_than_target = False,
    )
    ta.solve()
    # Resulting teams should all be of size 3 or less
    assert(all(ta.participants["team_num"].value_counts() >= 3))
    
