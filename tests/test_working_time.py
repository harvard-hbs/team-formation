import datetime
import os
import pandas as pd

from team_formation.working_time import working_times_hours

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_TIME_CSV = os.path.join(TEST_DIR, "data", "working_time_test.csv")

def test_working_time():
    roster = pd.read_csv(WORKING_TIME_CSV)
    roster["working_hour_list"] = working_times_hours(
        roster,
        datetime.date.today(),
        "time_zone",
        "working_time",
    )
    roster["working_hour_list"] = (
        roster["working_hour_list"].map(lambda hour_str: hour_str.split(";"))
    )
    sample_parti = roster.sample().iloc[0]
    print(sample_parti)
    
