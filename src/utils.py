import os.path
from  datetime import datetime, date, timedelta


BASE = os.path.join(os.path.dirname(__file__), "..")


def time_is_in(start, end):
    """Check if current time is between start and end.
    If end has already passed for current date, take it to be
    the next day. Ie. time_is_in('22:00', '07:00') returns True
    when called at 23:10.
    Args:
        start (str): start time in HH:MM
        end (str): end time in HH:MM
    """
    now = datetime.now()
    start_time = datetime.strptime(start, "%H:%M").time()
    end_time = datetime.strptime(end, "%H:%M").time()

    start = now.replace(
        hour=start_time.hour,
        minute=start_time.minute,
        second=start_time.second
    )
    end = now.replace(
        hour=end_time.hour,
        minute=end_time.minute,
        second=end_time.second
    )

    if now >= end:
        end = end + timedelta(1)

    return start <= now < end

def time_str_to_dt(s):
    """Convert a time string in HH:MM format to a datetime object. The date is set to
    current date if the time has not yet occured or the next day if it has.
    """
    today = date.today()
    dummy_dt = datetime.strptime(s, "%H:%M")

    dt = dummy_dt.replace(year=today.year, month=today.month, day=today.day)
    if dt <= datetime.now():
        dt = dt + timedelta(days=1)

    return dt
