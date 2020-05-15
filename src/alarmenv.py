#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os.path
import configparser
import dns.resolver
import dns.exception

from src import utils


logger = logging.getLogger("eventLogger")

class AlarmEnv:
    """Parses the configuration file to a readable object."""

    def __init__(self, config_file):
        """Setup an absolute path to the configuration file and a parser.
        params
            config_file (str): name (not path!) of the configuration file in /configs to use.
        """
        path_to_config = self.get_config_file_path(config_file)

        self.config_file = path_to_config
        self.config = configparser.ConfigParser()
        # Determine whether the host system is a Raspberry Pi by checking
        # the existance of a system brightness file.
        self.is_rpi = os.path.isfile("/sys/class/backlight/rpi_backlight/brightness")

    def setup(self):
        """Setup the environment: parse and validate the configuration file and test
        for network connectivity.
        """
        filenames = self.config.read(self.config_file)
        # config.read modifies the config object in place and returns list of file names read succesfully
        if not filenames:
            raise RuntimeError("Failed reading config file: {}".format(self.config_file))

        self.validate_config()

    def get_config_file_path(self, config_file):
        """Given a filename, look for an alarm configuration file from either:
          * $HOME/.alarmpi, or
          * BASE/configs
        Return:
            path to first detected config file or None is none found
        """
        PATHS_TO_CHECK = [
            os.path.expanduser("~/.alarmpi/" + config_file),
            os.path.join(utils.BASE, "configs", config_file)
        ]

        for path in PATHS_TO_CHECK:
            if os.path.isfile(path):
                logger.info("Using config file %s", os.path.normpath(path))
                return path

        raise FileNotFoundError("No valid configuration file found for {}".format(config_file))

    def _testnet(self):
        # Test for connectivity using the hostname in the config file
        nthost = self.config.get("main", "nthost")
        try:
            dns.resolver.query(nthost)
            return True
        except (dns.resolver.NXDOMAIN, dns.exception.DNSException):
            logger.warning("Could not resolve '%s'. Assuming the network is down.", nthost)
            return False

    def validate_config(self):
        """Validate configuration file: checks that
         1 content and tts sections have 'type', 'enabled' and 'handler' keys
         2 sections other than [main] have a 'type' key
         3 if a section with 'key_file' is enabled, the key points to an existing file
            (note: this does not valide the contents of the file!)
        """
        try:
            for section in self.get_sections(excludes=["main", "alarm", "polling", "greeting"]):
                section_type = self.get_value(section, "type")

                if section_type in ("content", "tts"):
                    self.get_value(section, "handler")  # raises NoOptionError if no 'handler' key
                    self.get_value(section, "enabled")

                # check for 'key_file' key on enabled sections
                key_file_match = self.config.has_option(section, "key_file")
                enabled = self.get_value(section, "enabled") == "1"
                # if found, check that it points to an existing file
                if key_file_match and enabled:
                    key_file_path = self.config.get(section, "key_file")
                    assert os.path.isfile(
                        key_file_path), "No such API keyfile: {}".format(key_file_path)

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise RuntimeError("Invalid configuration: ", e)

        return True

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

    def get_value(self, section, option, fallback=None):
        """Get a value matching a section and option. Raises either NoSectionError or
        NoOptionError on invalid input.
        """
        if fallback is None:
            return self.config.get(section, option)

        return self.config.get(section, option, fallback=fallback)
