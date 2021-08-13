#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Generates an alarm based on a configuration file and plays it. This module acts as
# the entry point to the actual alarm, and will be scheduled via cron.
# This module does not depend on the GUI and can therefore be scheduled manually
# to play an alarm.


import argparse

from src import alarm_builder
from src import apconfig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Play an alarm using a specified configuration file")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="default.yaml", help="alarm configuration file in ./configs to use. Defaults to default.yaml")
    args = parser.parse_args()

    config = apconfig.AlarmConfig(args.config)

    alarm = alarm_builder.Alarm(config)
    alarm.build_and_play()
