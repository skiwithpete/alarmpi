#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Entrypoint for the project, runs the clock GUI. The GUI can be used to
# schedule an alarm. To run the alarm directly, run alarm_builder.py.

import argparse
import sys
import os
import logging
import logging.config

from PyQt5.QtWidgets import QApplication

from src import clock


logging.config.fileConfig("logging.conf")
error_logger = logging.getLogger("errorLogger")
event_logger = logging.getLogger("eventLogger")



def backlight_excepthook(type, value, tb):
    """Custom exception handler for uncaught exceptions.
    From the docs (https://docs.python.org/3.7/library/sys.html#sys.excepthook):
        When an exception is raised and uncaught, the interpreter calls sys.excepthook with three arguments,
        the exception class, exception instance, and a traceback object. In an interactive session this happens
        just before control is returned to the prompt; in a Python program this happens just before the program
        exits. The handling of such top-level exceptions can be customized by assigning another three-argument
        function to sys.excepthook.

    If the program crashes due to an unpredictable cause, such as network error on API call, while the screen is blank
    it is difficult to turn it back on again (usually this means SSH'ing in and running stop.sh).
    By overwriting the default handler we can take care of this automatically.

    Note that screen blanking is disabled when the host system is not a Raspberry Pi.
    https://stackoverflow.com/questions/20829300/is-there-a-way-to-have-a-python-program-run-an-action-when-its-about-to-crash
    """
    import traceback
    import subprocess
    tbtext = "".join(traceback.format_exception(type, value, tb))
    error_logger.error(tbtext)

    BASE = os.path.dirname(__file__)
    path_to_stop_script = os.path.join(BASE, "stop.sh")

    # Call the stop script and log output
    process = subprocess.Popen(["/bin/bash", path_to_stop_script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    error_logger.info(output)


if __name__ == "__main__":
    sys.excepthook = backlight_excepthook

    parser = argparse.ArgumentParser(description="Run alarmpi GUI")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="default.yaml", help="Configuration file to use. Defaults to default.yaml")
    parser.add_argument("--fullscreen", action="store_true",
                        help="fullscreen mode")
    parser.add_argument("--debug", action="store_true",
                        help="debug mode")
    args = parser.parse_args()
    kwargs = {"fullscreen": args.fullscreen, "debug": args.debug}

    if args.debug:
        event_logger.info("Setting event_logger level to DEBUG")
        event_logger.setLevel(logging.DEBUG)
        for handler in event_logger.handlers:
            handler.setLevel(logging.DEBUG)

    app = QApplication(sys.argv)
    with open("src/style.qss") as f:
        app.setStyleSheet(f.read())

    ex = clock.Clock(args.config, **kwargs)
    ex.setup()
    res = app.exec_()

    sys.exit(res)
