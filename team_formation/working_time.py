import datetime
from zoneinfo import ZoneInfo

WORKING_HOURS = {
    "Morning": [7, 8, 9, 10, 11],
    "Afternoon": [12, 13, 14, 15, 16, 17],
    "Evening": [18, 19, 20, 21, 22],
}

INTERVAL_SEPARATOR = ";"

def working_times_hours(df, ref_date):
    """Convert `time_zone` and `working_time` to UTC start hours."""
    hours_list = []
    for i, row in df.iterrows():
        time_zone = row["time_zone"]
        working_time = row["working_time"]
        hours = working_time_hours(time_zone, working_time, ref_date)
        hours_str = INTERVAL_SEPARATOR.join(str(h) for h in hours)
        hours_list.append(hours_str)
    return hours_list

def working_time_hours(time_zone, working_times, ref_date):
    """Convert a time zone and string of working times into UTC start hours."""
    hour_list = []
    for wt in working_times.split("; "):
        wt_hours = WORKING_HOURS[wt]
        for wt_hour in wt_hours:
            wt_start_local = datetime.datetime(
                ref_date.year,
                ref_date.month,
                ref_date.day,
                wt_hour,
                0,
                0,
                tzinfo=ZoneInfo(time_zone)
            )
            wt_start_utc = wt_start_local.astimezone(datetime.timezone.utc)
            hour_utc = wt_start_utc.hour
            hour_list.append(hour_utc)
    return hour_list
