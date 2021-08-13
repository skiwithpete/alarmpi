import pytest
from freezegun import freeze_time

from src import utils


@pytest.mark.parametrize("start_time,end_time", [
    ("22:00", "07:00"),
    ("08:10", "18:20")
])
@freeze_time("2021-07-30 23:10")
def test_nighttime_with_night_hour(start_time, end_time):
    """Does time_is_in return True for:
      * overnight schedule
      * already passed end time (ie. is end time interpreted as next day)
    """
    assert utils.time_is_in(start_time, end_time)

@pytest.mark.parametrize("start_time,end_time", [
    ("22:00", "07:00"),
    ("18:00", "23:59")
])
@freeze_time("2021-07-30 11:10")
def test_nighttime_with_day_hour(start_time, end_time):
    """Does time_is_in return False for:
      * overnight schedule
      * schedule not containing current time
    """
    assert not utils.time_is_in(start_time, end_time)