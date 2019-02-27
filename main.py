#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import clock
import sys
from PyQt5.QtWidgets import QApplication


# Entrypoint for the project, runs the clock GUI. The GUI can be used to
# schedule an alarm. To run the alarm directly, run sound_the_alarm.py.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run alarmpi GUI")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="path to an alarm configuration file. Defaults to alarm.config")
    parser.add_argument("--fullscreen", action="store_true",
                        help="launch the script in fullscreen mode")
    args = parser.parse_args()
    kwargs = {"fullscreen": args.fullscreen}

    app = QApplication(sys.argv)
    ex = clock.Clock(args.config, **kwargs)
    ex.setup()
    sys.exit(app.exec_())
