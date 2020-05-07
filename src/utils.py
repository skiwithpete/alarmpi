#!/usr/bin/env python

import datetime


def weekend(d, offset, target_time):
    """Check whether a datetime d is during a weekend. A weekend
    is defined as friday target_time to monday target_time - offset
    Args:
        d (datetime): the datetime to test
        offset (int): hour offset
        target_time (str): time in %H:%M format to compare test_time against
    """
    is_nighttime = nighttime(d, offset, target_time)
    dow = d.weekday()  # 0 == monday

    friday = (dow == 4 and not is_nighttime)  # daytime during friday
    saturday = (dow == 5)  # all of saturday
    sunday = (dow == 6 and not is_nighttime)  # daytime during sunday

    return (friday or saturday or sunday)

def nighttime(d, offset, target_time):
    """Check whether the time part of a datetime d is within offset hours
    from target_time.
    Args:
        d (datetime): the datetime whose time value to test
        offset (int): hour offset
        target_time (str): time in %H:%M format to compare test_time against
    """
    d_minutes = datetime_to_minutes(d)
    target_time_minutes = time_str_to_minutes(target_time)
    offset_minutes = offset * 60

    # Case 1: d is after midnight and before target_time: check if d is
    # within offset
    if d_minutes < target_time_minutes:
        return abs(d_minutes - target_time_minutes) < offset_minutes

    # Case 2: d is before midnight and after target_time:
    # compute (d's distance to midnight) + target_time_minutes and
    # compare to offset
    if d_minutes > target_time_minutes:
        MAX_MINUTES = 23*60 + 59
        minutes_to_target_time = (MAX_MINUTES - d_minutes) + target_time_minutes
        return minutes_to_target_time < offset_minutes

    return True

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
