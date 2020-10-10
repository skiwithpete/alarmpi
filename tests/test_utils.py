import pytest

from src import utils




@pytest.mark.parametrize("compare_time,target_time", [
    ("01:14", "07:02"),
    ("12:54", "19:20"),
])
def test_nighttime_with_night_hour(compare_time, target_time):
    """Does nightime return True when called with compare_times matching
    the targeted nighttime offset?
    """
    offset = 8
    assert utils.nighttime(target_time, offset, compare_time)

@pytest.mark.parametrize("compare_time,target_time", [
    ("22:14", "07:02"),
    ("07:05", "07:00"),
])
def test_nighttime_with_day_hour(compare_time, target_time):
    """Does nightime return False when called with compare_times outside of
    target_time thresholds?
    """
    offset = 8
    assert not utils.nighttime(target_time, offset, compare_time)

