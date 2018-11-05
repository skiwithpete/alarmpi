#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import sys
import configparser
import dns.resolver
import dns.exception


class AlarmEnv:
    """Parses the configuration file to a readable object."""

    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

    def setup(self):
        """Setup the environment: parse and validate the configuration file and test
        for network connectivity.
        """
        filenames = self.config.read(self.config_file)
        # config.read modifies the config object in place and returns list of file names read succesfully
        if not filenames:
            raise RuntimeError("Failed reading config file: {}".format(self.config_file))

        self.validate_config()
        self.radio_url = self.get_value("radio", "url")
        self.netup = self._testnet()

    def _testnet(self):
        # Test for connectivity using the hostname in the config file
        nthost = self.config.get("main", "nthost")
        try:
            dns.resolver.query(nthost)
            return True
        except (dns.resolver.NXDOMAIN, dns.exception.DNSException):
            print("Could not resolve '{}'. Assuming the network is down.".format(nthost))
            return False

    def validate_config(self):
        """Validate configuration file: checks that
         1 content and tts sections have 'type', 'enabled' and 'handler' keys
         2 sections other than [main] have a 'type' key
        """
        try:
            for section in self.get_sections(excludes=["main"]):
                section_type = self.get_value(section, "type")

                if section_type in ("content", "tts"):
                    self.get_value(section, "handler")
                    self.get_value(section, "enabled")

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise RuntimeError("Invalid configuration: ", e)

        return True

    def write_default_configuration(self):
        """Create a default configuration set and write as alarm.config."""
        path = os.path.abspath("alarm.config")
        if os.path.isfile(path):
            ans = input("Overwrite existing configuration?")
            if ans.lower() != "y":
                sys.exit()

        # default config as a single string
        config = """
        [main]
        readaloud=1
        nthost=translate.google.com
        end=Thats all for now. Have a nice day.

        ###################
        # Content sources #
        ###################
        # Note: items are processed in listed order, ie. greeting should come first

        [greeting]
        enabled=1
        type=content
        handler=get_greeting.py
        # Name for personalized greeting, leave empty for a generalized 'Goog morning' message
        name=

        [yahoo_weather]
        enabled=1
        type=content
        handler=get_yahoo_weather.py
        # Find your location here: http://woeid.rosselliot.co.nz/
        location=564617
        unit=c
        # Change temperature unit to Fahrenheit with 'f'
        wind=1
        wind_chill=1

        [BBC_news]
        enabled=1
        type=content
        handler=get_bbc_news.py

        ###############
        # TTS engines #
        ###############
        # Notes:
        # 1 order implies preference for enabled tts engines
        # 2 at most one tts engine is used
        # 3 if readaloud=0 in the [main] section, no tts engine will be used

        [google_gcp_tts]
        enabled=0
        type=tts
        # generate your own service key from Google Cloud console and set path to it
        private_key_file=
        handler=get_gcp_tts.py

        [google_translate_tts]
        enabled=1
        type=tts
        handler=get_google_translate_tts.py

        [festival_tts]
        enabled=0
        type=tts
        handler=get_festival_tts.py


        #############
        # Misc taks #
        #############
        [radio]
        type=radio
        # url for an internet radio stream, leave empty to disable radio
        url=
        """
        with open(path, "w") as f:
            f.write(config)

    def config_has_match(self, section, option, value):
        """Check if config has a section and a key/value pair matching input."""
        try:
            section_value = self.get_value(section, option)
            return section_value == value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return False
        except ValueError:
            raise ValueError("Invalid configuration for {} in section {}".format(option, section))

    # ========================================================================#
    # The following get_ functions are mostly wrappers to get various values from
    # the configuration file (ie. self.config)

    def get_sections(self, excludes=None):
        """Return a list of section names in the configuration file."""
        sections = self.config.sections()
        if excludes is None:
            excludes = []

        return [s for s in sections if s not in excludes]

    def get_enabled_sections(self, section_type):
        """Return names of sections sections whose 'type' is section_type (either 'content' or 'tts')."""
        sections = [s for s in self.get_sections(excludes=["main"]) if
                    self.config_has_match(s, "type", section_type) and
                    self.config_has_match(s, "enabled", "1")
                    ]
        return sections

    def get_section(self, section):
        """Return a configuration section by name."""
        return self.config[section]

    def get_value(self, section, option):
        """Get a value matching a section and option. Throws either NoSectionError or
        NoOptionError on invalid input.
        """
        return self.config.get(section, option)

    def get_value_with_fallback(self, section, option, fallback):
        """Get a value matching a section and option, but return a fallback value on
        invalid input instead of raising an error.
        """
        return self.config.get(section, option, fallback=fallback)
