#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Generates an alarm based on a configuration file and plays it. This module acts as
# the entry point to the actual alarm, and will be scheduled via cron.
# This module does not depend on the GUI and can therefore be scheduled manually
# to play an alarm.


import argparse

from src import alarm_builder
from src import alarmenv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Play an alarm using a specified configuration file")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="path to an alarm configuration file. Defaults to alarm.config")
    args = parser.parse_args()

    env = alarmenv.AlarmEnv(args.config)
    env.setup()

    alarm = alarm_builder.Alarm(env)
    alarm.build_and_play()
