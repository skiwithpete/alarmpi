#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import importlib
import os
import inspect
import signal

import pydub
import pydub.playback

from src.handlers import get_festival_tts


# get path to the root folder
BASE = os.path.join(os.path.dirname(__file__), "..")
PIDFILE = os.path.join(BASE, "pidfile")

# alias USRSIGnals for clarity
RADIO_PLAY_SIGNAL = signal.SIGUSR1
SCREEN_WAKEUP_SIGNAL = signal.SIGUSR2


class Alarm:

    def __init__(self, env):
        self.env = env

    def build_and_play(self):
        """Read the configuration file, create and play the corresponding alarm."""
        tts_enabled = self.env.config_has_match("main", "readaloud", "1")
        pid = Alarm.gui_running()

        # If no network connection is detected, or the 'readaloud' option is not set,
        # paly a beeping sound effect isntead of making a series of API calls.
        if not self.env.netup or not tts_enabled:
            if pid:
                os.kill(pid, SCREEN_WAKEUP_SIGNAL)
            Alarm.play_beep()
            return

        content = self.generate_content()
        tts_client = self.get_tts_client()
        text = "\n".join(content)
        if pid:
            os.kill(pid, SCREEN_WAKEUP_SIGNAL)
        tts_client.play(text)

        # Play the radio stream if enabled:
        # If the GUI is running, send a signal to it to use its RadioStreamer.
        # Signalling also sets the GUI's radio button as pressed.
        # If GUI is not running, call mplayer directly.
        if self.env.config_has_match("radio", "enabled", "1"):
            if pid:
                os.kill(pid, RADIO_PLAY_SIGNAL)
            else:
                self.play_radio()

    def sound_alarm_without_gui_or_radio(self):
        """A stripped down version of main above. Play TTS sections of the alarm
        without sending signals to the GUI or playing the radio.
        """
        if not self.env.netup:
            Alarm.play_beep()
            return

        content = self.generate_content()
        tts_client = self.get_tts_client()
        text = "\n".join(content)
        tts_client.play(text)

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
            try:
                parser.build()
            except KeyError as e:
                print("Error: missing key {} in configuration file.".format(e))
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
            key_file = self.env.get_value(tts_section, "key_file", fallback=False)
            client = class_(keyfile=key_file)

        # by default, use Festival tts client
        else:
            client = get_festival_tts.FestivalTTSManager()

        return client

    def get_content_parser_class(self, section_name):
        """Given config file handler section name, return the class of the handler."""
        # use importlib to dynamically import the correct module within
        # the 'handlers' package.
        handler_module_name = self.env.get_value(section_name, "handler")[:-3]
        path_to_module = "src.handlers.{}".format(handler_module_name)
        handler_module = importlib.import_module(path_to_module)

        # Inspect the handler module for classes and return the first class.
        # Note: assumes there is excatly one class in each handler module!
        class_ = inspect.getmembers(handler_module, inspect.isclass)[0][1]

        return class_

    def play_radio(self):
        """Play the radio stream defined in the configuration using mplayer."""
        args = self.env.get_value("radio", "args")
        cmd = "/usr/bin/mplayer {}".format(args).split()
        # Run the command via Popen directly to open the stream as a child process without
        # waiting for it to finish.
        subprocess.Popen(cmd)

    @staticmethod
    def gui_running():
        """Determine whether the GUI is running from the existance of the pidfile.
        Return the pid if running.
        """
        try:
            with open(PIDFILE) as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return False

    @staticmethod
    def play_beep():
        """Play a beeping sound effect."""
        path = os.path.join(BASE, "resources", "Cool-alarm-tone-notification-sound.mp3")
        beep = pydub.AudioSegment.from_mp3(path)
        pydub.playback.play(beep)

        return path
