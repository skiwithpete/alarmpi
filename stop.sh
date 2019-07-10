#!/bin/bash
# kill the alarm (if running). Useful for killing radio stream started by cron
pkill mplayer
pkill -f "play_alarm.py"  # only kill the python process running the alarm
pkill -f "python .*(alarmpi/)?main.py"

# ensure backlight is turned on
echo 0 > /sys/class/backlight/rpi_backlight/bl_power
