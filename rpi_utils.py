#!/usr/bin/env python

"""
Collectin of Raspberry Pi related helper functions for interacting with screen
brightness.
"""

import subprocess


def toggle_display_backlight_brightness():
    """Reads Raspberry pi touch display's current brightness values from system
    file and sets it to either high or low depending on the current value.
    """
    PATH = "/sys/class/backlight/rpi_backlight/brightness"
    LOW = 9
    HIGH = 255

    with open(PATH) as f:
        brightness = int(f.read())

    # set to furthest away from current brightness
    if abs(brightness-LOW) < abs(brightness-HIGH):
        new_brightness = HIGH
    else:
        new_brightness = LOW

    with open(PATH, "w") as f:
        f.write(str(new_brightness))


def toggle_screen_blank(state="on"):
    """Use xset utility to toggle the screen state between screensaver (ie. blank)
    and active (the default).
    Touching the screen will also activate the screen.
    """
    cmd = "xset s reset".split()
    if state == "on":
        cmd = "xset s activate".split()

    env = {"XAUTHORITY": "/home/pi/.Xauthority", "DISPLAY": ":0"}
    subprocess.run(cmd, env=env)


def get_screen_state():
    """Get the current screen state using xset utility: is it currently blank?
    returns True if screen is active?
    """
    cmd = "xset q".split()
    res = subprocess.check_output(cmd)
    return "Monitor is On" in str(res)
