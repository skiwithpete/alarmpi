#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import argparse
import importlib
import os.path
import os
import sys
import inspect
import signal

import pydub
import pydub.playback
import alarmenv


class Alarm:
    """A wrapper class for playing the alarm. Createa and alarmenv.AlarmEnv object based on
    the configuration file and uses it to create the approriate alarm.
    """

    def __init__(self, config_file):
        self.env = alarmenv.AlarmEnv(config_file)
        self.env.setup()

    def main(self):
        """Read the configuration file, create and play the corresponding alarm."""
        # Check status for internet connection. If no connection detected,
        # play a beeping sound instead of making API calls.
        if not self.env.netup:
            Alarm.play_beep()

        else:
            tts_enabled = self.env.config_has_match("main", "readaloud", "1")
            if tts_enabled:
                content = self.generate_content()
                tts_client = self.get_tts_client()
                text = "\n".join(content)
                tts_client.play(text)

            # play a beeping sound if readaloud is not enabled
            else:
                Alarm.play_beep()

            # Play the radio stream if enabled:
            # If the GUI is running, send a signal to it to use its RadioStreamer
            # to handle necessary GUI buttons and process control,
            # otherwise call mplayer directly.
            if self.env.radio_url:
                pid = Alarm.gui_running()
                if pid:
                    os.kill(pid, signal.SIGUSR1)  # send a user signal
                else:
                    self.play_radio()

    def generate_content(self):
        """Loop through the configuration file and process each enabled item."""
        content_sections = self.env.get_enabled_sections("content")

        # for each section get the handler module and create the approriate
        # instance
        contents = []
        for section_name in content_sections:
            class_ = self.get_content_parser_class(section_name)

            # create an instance using the config section name
            section = self.env.get_section(section_name)
            parser = class_(section)

            # call build to run the parser and store output
            parser.build()
            contents.append(parser.get())

        # add ending phrase from the config file
        contents.append(self.env.get_value("main", "end"))

        for section in contents:
            print(section)

        return contents

    def get_tts_client(self):
        """Determine which TTS engine to use based on the enabled tts sections
        in the config file. First enabled section is used.
        """
        tts = self.env.get_enabled_sections("tts")

        # Instantiate the correct class
        if tts:
            tts_section = tts[0]
            class_ = self.get_content_parser_class(tts_section)
            # read the path to the keyfile if provided/applicable
            key_file = self.env.get_value_with_fallback(tts_section, "private_key_file", None)
            client = class_(keyfile=key_file)

        # by default, use Festival tts client
        else:
            from handlers import get_festival_tts
            client = get_festival_tts.FestivalTTSManager()

        return client

    def get_content_parser_class(self, section_name):
        """Given config file handler section name, return the class of the handler."""
        # use importlib to dynamically import the correct module within
        # the 'handlers' package.
        handler_module_name = self.env.get_value(section_name, "handler")[:-3]
        path_to_module = "handlers.{}".format(handler_module_name)
        handler_module = importlib.import_module(path_to_module)

        # Inspect the handler module for classes and return the first class.
        # Note: assumes there is excatly one class in each handler module!
        class_ = inspect.getmembers(handler_module, inspect.isclass)[0][1]

        return class_

    def play_radio(self):
        """Play the radio stream defined in the configuration using mplayer."""
        cmd = "/usr/bin/mplayer -quiet -nolirc -playlist {} -loop 0".format(
            self.env.radio_url).split()
        # Run the command via Popen directly to open the stream as a child process without
        # waiting for it to finish.
        subprocess.Popen(cmd)

    @staticmethod
    def gui_running():
        """Check if the GUI is running. Attempts to read the GUI's pid from it's
        pidfile.
        """
        import main
        try:
            with open(main.PIDFILE) as f:
                pid = int(f.read())
                return pid
        except FileNotFoundError:
            return

    @staticmethod
    def play_beep():
        """Play a beeping sound effect."""
        # Create a path to the mp3 file. If this script was called via cron, we need
        # an absolute path. Since cron runs this script with absolute paths as
        # /path/to/python /path/to/sound_the_alarm.py /path/to/alarm.config we can
        # use sys.argv to format an absolute path to the sound file.
        # This is a bit of a hack, there's probably a better way...

        path = os.path.abspath("resources/Cool-alarm-tone-notification-sound.mp3")
        if len(sys.argv) > 1:
            base = os.path.dirname(sys.argv[1])  # get dirname from sound_the_alarm.py
            path = os.path.join(base, "resources", "Cool-alarm-tone-notification-sound.mp3")

        beep = pydub.AudioSegment.from_mp3(path)
        pydub.playback.play(beep)

        return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Play the alarm using a specified configuration file")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="path to an alarm configuration file. Defaults to alarm.config")
    parser.add_argument("--init-config", action="store_true",
                        help="re-create the default configuration file alarm.config. Overwrites existing file.")
    args = parser.parse_args()

    app = Alarm(args.config)

    if args.init_config:
        app.env.write_default_configuration()

    else:
        app.main()
