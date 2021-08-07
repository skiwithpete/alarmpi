import subprocess
import re
import os.path
from datetime import datetime, date, timedelta

from PyQt5.QtGui import QPixmap


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

def get_volume():
    """Get current volume level from amixer as integer from 0 to 100."""
    res = subprocess.run("amixer -c 1 sget PCM".split(), capture_output=True)

    # Response contains volume level as percentage, parse the digits
    s = re.search("\[(\d*)%\]", res.stdout.decode("utf8"))
    return int(s.group(1))

def set_volume(level):
    subprocess.run("amixer --quiet -c 1 sset PCM {}%".format(level).split())

def get_volume_icon(mode):
    """Determine icon set to use as volume level. If Adwaita Ubuntu theme exists use its icons.
    Otherwise use custom icons.
    Args:
        mode (str): volume level: muted/low/medium/high
    Return:
        QPixmap object matching the mode
    """

    SYSTEM_THEME_BASE = "/usr/share/icons/Adwaita/32x32/status/"
    if os.path.isfile(os.path.join(SYSTEM_THEME_BASE, "audio-volume-high-symbolic.symbolic.png")):
        img_map = {
            "muted": os.path.join(SYSTEM_THEME_BASE, "audio-volume-muted-symbolic.symbolic.png"),
            "low": os.path.join(SYSTEM_THEME_BASE, "audio-volume-low-symbolic.symbolic.png"),
            "medium": os.path.join(SYSTEM_THEME_BASE, "audio-volume-medium-symbolic.symbolic.png"),
            "high": os.path.join(SYSTEM_THEME_BASE, "audio-volume-high-symbolic.symbolic.png")
        }
        return QPixmap(img_map[mode])

    else:
        original = QPixmap(os.path.join(BASE, "resources", "icons", "volume_640.png"))
        Y = 70
        HEIGHT = 212

        img_map = {
            "muted": original.copy(0, Y, 172, HEIGHT),
            "low": original.copy(165, Y, 198, HEIGHT),
            "medium": original.copy(165, Y, 198, HEIGHT), # same as low
            "high": original.copy(375, Y, 258, HEIGHT)
        }

        return img_map[mode].scaledToHeight(32)
