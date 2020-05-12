#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import importlib
import os
import inspect
import signal

import pydub
import pydub.playback

from src import utils
from src.handlers import get_festival_tts, get_greeting


class Alarm:

    def __init__(self, env):
        self.env = env

    def build(self):
        """Loop through the configuration file for enabled content sections
        and generate content.
        Return:
            list of generated content
        """
        contents = []

        # Initialize content with greeting
        contents.append(self.generate_greeting())
       
        # For each content section get the handler module and create the approriate
        # instance
        content_sections = self.env.get_enabled_sections("content")
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

        # Add ending phrase from the config file
        contents.append(self.env.get_value("main", "end"))

        for section in contents:
            print(section)

        return contents

    def play(self, content):
        """Play an alarm.
        Args:
            content (list): list of various contents to play via TTS. Each list item
            item should be the text to 
        """
        tts_enabled = self.env.config_has_match("main", "readaloud", "1")

        # If no network connection is detected, or the 'readaloud' option is not set,
        # return None to signify alarm player should play beep instead.
        if not self.env.netup or not tts_enabled:
            Alarm.play_beep()

        else:
            tts_client = self.get_tts_client()
            content_text = "\n".join(content)
            tts_client.play(content_text)

    def build_and_play(self):
        """Build and play an alarm.
        This is provided as a CLI method of playing the alarm. This has some differences
        compared to the GUI based alarm behavior in alarm.py:
          * since building and playing is chained together there may be an upto 3 delay
            on playing the alarm.
          * radio playback is handled directly rather than using alarm.py's custom thread.
        """
        content = self.build()
        self.play(content)

        # Play the radio stream if enabled
        if self.env.config_has_match("radio", "enabled", "1"):
            self.play_radio()

    def generate_greeting(self):
        """Generate a greeting using get_greeting.py handler.
        Return:
            the greeting as string.
        """
        section = self.env.get_section("greeting")
        greeter = get_greeting.Greeting(section)
        greeter.build()
        return greeter.get()

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
    def play_beep():
        """Play a beeping sound effect."""
        path = os.path.join(utils.BASE, "resources", "Cool-alarm-tone-notification-sound.mp3")
        beep = pydub.AudioSegment.from_mp3(path)
        pydub.playback.play(beep)

        return path
