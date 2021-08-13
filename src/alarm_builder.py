#!/usr/bin/env python

# Generates alarm content based on configuration file.


import subprocess
import importlib
import os
import inspect

import pydub
import pydub.playback

from src import utils
from src.handlers import get_festival_tts, get_greeting


class Alarm:

    def __init__(self, config):
        self.config = config

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
        # content parser
        content_sections = self.config.get_enabled_sections("content")
        for section in content_sections:
            class_ = self.get_content_parser_class(content_sections[section])
            parser = class_(content_sections[section])

            # call build to run the parser and store output
            try:
                parser.build()
            except KeyError as e:
                print("Error: missing key {} in configuration file.".format(e))
            contents.append(parser.get())

        # Add ending phrase from the config file
        contents.append(self.config["main"].get("end", ""))

        for section in contents:
            print(section)

        return contents

    def play(self, content):
        """Play an alarm. Either send alarm content to TTS client or play a beeping
        sound effect.
        Args:
            content (list): list of various contents to play via TTS. Each list item
            item should be the text to
        """
        tts_enabled = self.config["main"]["TTS"]

        # If no network connection is detected, or TTS is not enabled play beep
        if not self.config._testnet() or not tts_enabled:
            Alarm.play_beep()
            return

        tts_client = self.get_tts_client()  # First enabled client
        content_text = "\n".join(content)
        tts_client.play(content_text)

    def build_and_play(self):
        """Build and play an alarm.
        This is provided as a CLI interface for playing the alarm.
        Since the alarm is built on the go, there may be a few seconds delay on play.
        """
        content = self.build()
        self.play(content)

        # Play the radio stream if enabled
        if self.config["radio"]["enabled"]:
            self.play_radio()

    def generate_greeting(self):
        """Generate a greeting using get_greeting.py handler.
        Return:
            the greeting as string.
        """
        section = self.config["content"]["greeting"]
        greeter = get_greeting.Greeting(section)
        greeter.build()
        return greeter.get()

    def get_tts_client(self):
        """Determine which TTS engine to use based on the enabled tts sections
        in the config file. First enabled section is used.
        """
        # Valid config can only have 1 enabled TTS engine. Note that
        # response is a wrapper containing dicionary with the top level TTS key.
        section_wrapper = self.config.get_enabled_sections("TTS")
        
        # Instantiate the correct class
        if section_wrapper:
            section = list(section_wrapper.values())[0]

            class_ = self.get_content_parser_class(section)
            # read the path to the keyfile if provided/applicable
            credentials = section.get("credentials")
            client = class_(credentials=credentials)

        # by default, use Festival tts client
        else:
            client = get_festival_tts.FestivalTTSManager()

        return client

    def get_content_parser_class(self, section):
        """Given config file section name, return the class matching the handler."""
        # use importlib to dynamically import the correct module within
        # the 'handlers' package.
        path_to_module = "src.handlers.{}".format(section["handler"][:-3])
        handler_module = importlib.import_module(path_to_module)

        # Inspect the handler module for classes and return the first class.
        class_ = inspect.getmembers(handler_module, inspect.isclass)[0][1]

        return class_

    def play_radio(self):
        """Open a stream to the default radio station using cvlc."""
        default_station = self.config["radio"]["default"]
        url = self.config["radio"]["urls"][default_station]

        args = self.config["radio"].get("args", "")
        cmd = "/usr/bin/cvlc {} {}".format(url, args).split()
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
