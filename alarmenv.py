#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import sys
import configparser
import dns.resolver
import dns.exception


# Parses the configuration file (by default alarmpi.config) to a dict

class AlarmEnv:

    def __init__(self, config_file, debug=False):
        """Read configurations from file."""
        # Create a ConfigParser and read the config file
        self.config = configparser.ConfigParser()

        # make sure config_file is an absolute path for cron
        # TODO cron's current working directory is home folder -> this won't work
        config_file = os.path.abspath(config_file)  # does nothing is already an absolute path
        filenames = self.config.read(config_file)
        # config.read modifies the config object in place and returns list of file names read succesfully
        if not filenames:
            raise RuntimeError('Failed reading config file: {}'.format(config_file))

        self.validate_config()

        # Check if debug option was specified either thought the config file of command line
        self.debug = debug or self.config_has_match('main', 'debug', '1')

        # We still want to alarm if the net is down
        self._testnet()

    def _testnet(self):
        # Test for connectivity using the hostname in the config file
        nthost = self.config.get("main", "nthost")
        try:
            dns.resolver.query(nthost)
            self.netup = True
        except (dns.resolver.NXDOMAIN, dns.exception.DNSException):
            self.netup = False
            if self.debug:
                print('Could not resolve "{}". Assuming the network is down.'.format(nthost))

    def config_has_match(self, section, option, value):
        """Check if config has a section and a key/value pair matching input."""
        try:
            section_value = self.config.get(section, option)
            return section_value == value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return False
        except ValueError:
            raise ValueError("Invalid configuration for {} in section {}".format(option, section))

    def validate_config(self):
        """Validate configuration file: checks that other than [main] each section
        has 'type' and 'enabled' keys and that contents have a 'handler'.
        """
        try:
            for section in self.get_sections(exclude_main=True):
                section_type = self.get_value(section, "type")
                self.get_value(section, "enabled")

                if section_type == "content":
                    self.get_value(section, "handler")

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
        debug=0
        readaloud=1
        nthost=translate.google.com
        # Keep the trailing '/' on ramfldr
        ramfldr=/mnt/ram/
        end=Thats all for now. Have a nice day.

        ###################
        # Content sources #
        ###################
        # Note: items are processed in listed order, ie. greeting should come first

        [greeting]
        enabled=1
        type=content
        standalone=1
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
        private_key_file=Alarmpi-cdb50622e298.json
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
        enabled=1
        type=radio
        url=https://www.yle.fi/livestream/radiosuomi.asx
        """
        with open(path, "w") as f:
            f.write(config)

    # ========================================================================#
    # The following get_ functions are mostly wrappers to get various values from
    # the configuration file (ie. self.config)

    def get_sections(self, exclude_main=False):
        """Return a list of sections in the configuration file with or without
        the 'main' section.
        """
        sections = self.config.sections()
        if exclude_main:
            return [s for s in sections if s != "main"]

        return sections

    def get_enabled_content_sections(self):
        """Return names of enabled sections whose 'type' is 'content'."""
        sections = [s for s in self.get_sections(exclude_main=True) if
                    self.config_has_match(s, "type", "content") and
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
