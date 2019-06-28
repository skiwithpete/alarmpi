#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Entrypoint for the project, runs the clock GUI. The GUI can be used to
# schedule an alarm. To run the alarm directly, run alarm_builder.py.

import argparse
import sys
import os
import logging

from PyQt5.QtWidgets import QApplication

from src import clock
from src import alarm_builder


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def write_pidfile():
    pid = os.getpid()
    with open(alarm_builder.PIDFILE, "w") as f:
        f.write(str(pid))


def clear_pidfile():
    os.remove(alarm_builder.PIDFILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run alarmpi GUI")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="Configuration file to use. Defaults to alarm.config")
    parser.add_argument("--fullscreen", action="store_true",
                        help="fullscreen mode")
    parser.add_argument("--debug", action="store_true",
                        help="debug mode")
    args = parser.parse_args()
    kwargs = {"fullscreen": args.fullscreen, "debug": args.debug}

    app = QApplication(sys.argv)
    write_pidfile()

    ex = clock.Clock(args.config, **kwargs)
    ex.setup()
    res = app.exec_()
    clear_pidfile()

    sys.exit(res)
