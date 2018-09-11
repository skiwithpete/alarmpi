#!/bin/bash
# kill the alarm (if running). Useful for killing radio stream
# started by cron
pkill mplayer
pkill -f "sound_the_alarm.py"  # only kill the python process running the alarm
