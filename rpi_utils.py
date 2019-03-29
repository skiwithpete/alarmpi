#!/usr/bin/env python

"""
Collectin of Raspberry Pi related helper functions for interacting with screen
brightness.
"""
import os
import subprocess


def set_display_backlight_brightness(brightness):
    """Set backlight brithness to value between 0 and 255."""
    assert brightness >= 0 and brightness <= 255

    PATH = "/sys/class/backlight/rpi_backlight/brightness"
    with open(PATH, "w") as f:
        f.write(str(brightness))


def get_display_backlight_brightness():
    """Return the current backlight brightness value."""
    PATH = "/sys/class/backlight/rpi_backlight/brightness"
    with open(PATH) as f:
        return int(f.read().strip())


def toggle_display_backlight_brightness():
    """Reads Raspberry pi touch display's current brightness values from system
    file and sets it to either high or low depending on the current value.
    """
    LOW = 9
    HIGH = 255

    brightness = get_display_backlight_brightness()

    # set to furthest away from current brightness
    if abs(brightness-LOW) < abs(brightness-HIGH):
        new_brightness = HIGH
    else:
        new_brightness = LOW

    set_display_backlight_brightness(new_brightness)


def toggle_screen_state(state="on"):
    """Toggle screen state between on / off."""
    PATH = "/sys/class/backlight/rpi_backlight/bl_power"

    value = 1
    if state == "on":
        value = 0

    with open(PATH, "w") as f:
        f.write(str(value))


def screen_is_powered():
    """Determine whether the screen backlight is currently on."""
    PATH = "/sys/class/backlight/rpi_backlight/bl_power"
    with open(PATH) as f:
        value = f.read().strip()

    return value == "0"


def get_and_set_screen_state(new_state):
    """Read the current screen power state and set it to new_state. Returns the
    previous value.
    """
    PATH = "/sys/class/backlight/rpi_backlight/bl_power"
    with open(PATH, "r+") as f:
        previous_value = f.read().strip()

        f.seek(0)
        value = 1
        if new_state == "on":
            value = 0
        f.write(str(value))

    return previous_value


def toggle_screen_state_xset(state="on"):
    """Use xset utility to turn the screen on (the default)/off.
    Touching the screen will also activate the screen.
    """
    cmd = "xset dpms force on".split()
    if state == "off":
        cmd = "xset dpms force off".split()

    home = os.path.expanduser("~")
    xauthority = os.path.join(home, ".Xauthority")
    env = {"XAUTHORITY": xauthority, "DISPLAY": ":0"}
    subprocess.run(cmd, env=env)


def screen_is_powered_xset():
    """Use xset to get the current screen state: is it currently blank?
    returns True if screen is active
    """
    cmd = "xset q".split()
    res = subprocess.check_output(cmd)
    return "Monitor is On" in str(res)
