#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import clock


# Entrypoint for the project, runs the clock GUI. The rest of the components
# (greeting, news and weather, radio) are processed in sound_the_alarm.py. The clock
# can be used to set a cron entry for this. Alternatively, sound_the_alarm.py
# can be run directly.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run alarmpi GUI")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="path to an alarm configuration file")
    parser.add_argument("--windowed", action="store_true")
    args = parser.parse_args()

    kwargs = {"windowed": args.windowed}
    app = clock.Clock(args.config, **kwargs)
    app.run()
