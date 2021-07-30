import os.path
import datetime


BASE = os.path.join(os.path.dirname(__file__), "..")


def nighttime(target_time, offset, compare_time=None):
    """Check whether compare_time is within offset hours of target_time.
    Args:
        target_time (str): target time for the test in HH:MM.
        offset (int): hour offset
        compare_time (str): the time to test in HH:MM, defaults to
            current time
    """
    dummy_base_date = datetime.date.today()

    # convert times from strtings to datetimes with date set to today
    target_dt = datetime.datetime.strptime(target_time, "%H:%M")
    target_dt = target_dt.replace(
        year=dummy_base_date.year,
        month=dummy_base_date.month,
        day=dummy_base_date.day
    )

    if compare_time is not None:
        compare_dt = datetime.datetime.strptime(compare_time, "%H:%M")
        compare_dt = compare_dt.replace(
            year=dummy_base_date.year,
            month=dummy_base_date.month,
            day=dummy_base_date.day
        )

    else:
        compare_dt = datetime.datetime.now()

    offset_target_dt = target_dt - datetime.timedelta(hours=offset)
    return compare_dt >= offset_target_dt and compare_dt <= target_dt

def time_str_to_minutes(s):
    """Convert a time string in %H:%M format to minutes since midnight."""
    input_time = datetime.datetime.strptime(s, "%H:%M")
    return input_time.hour * 60 + input_time.minute

def datetime_to_minutes(d):
    """Convert a datetime into minutes since midnight."""
    return d.hour * 60 + d.minute

def time_str_to_dt(s):
    """Convert a time string in HH:MM format to a datetime object. The date is set to
    current date if the time has not yet occured or the next day if it has.
    """
    today = datetime.date.today()
    dummy_dt = datetime.datetime.strptime(s, "%H:%M")

    dt = dummy_dt.replace(year=today.year, month=today.month, day=today.day)
    if dt <= datetime.datetime.now():
        dt = dt + datetime.timedelta(days=1)

    return dt
