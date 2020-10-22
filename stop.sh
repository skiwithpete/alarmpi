#!/bin/bash
# kill the alarm (if running). Useful for killing radio stream started by cron
pkill mplayer
pkill -f "play_alarm.py"  # only kill the python process running the alarm
pkill -f "python .*(alarmpi/)?main.py"

# Ensure backlight is turned on (only on Raspberry Pi)
FILE=/sys/class/backlight/rpi_backlight/bl_power
if [[ -f "$FILE" ]]; then
    echo 0 > /sys/class/backlight/rpi_backlight/bl_power
    echo 255 > /sys/class/backlight/rpi_backlight/brightness
fi

