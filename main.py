#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import clock


# Entrypoint for the project, runs the clock GUI. The rest of the components
# (greeting, news and weather, radio) are processed in sound_the_alarm.py. The clock
# can be used to set a cron entry for this. Alternatively, sound_the_alarm.py
# can be run directly.

# file location for storing the GUI's pid
PIDFILE = "alarmgui.pid"


def write_pidfile():
    """Write a pidfile for the currently running Python process (ie. main.py)"""
    pid = str(os.getpid())
    with open(PIDFILE, "w") as f:
        f.write(pid)


def remove_pidfile():
    os.remove(PIDFILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run alarmpi GUI")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="path to an alarm configuration file. Defaults to alarm.config")
    parser.add_argument("--fullscreen", action="store_true",
                        help="launch the script in fullscreen mode")
    args = parser.parse_args()

    write_pidfile()
    kwargs = {"fullscreen": args.fullscreen}
    app = clock.Clock(args.config, **kwargs)
    app.run()
    remove_pidfile()
