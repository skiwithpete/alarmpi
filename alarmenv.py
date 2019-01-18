#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
         3 if a section with 'key_file' is enabled, the key is non-empty
            (note: this does not valide the file!)
        """
        try:
            for section in self.get_sections(excludes=["main", "alarm"]):
                section_type = self.get_value(section, "type")

                if section_type in ("content", "tts"):
                    self.get_value(section, "handler")  # raises NoOptionError if no 'handler' key
                    self.get_value(section, "enabled")

                # check for 'key_file' key on enabled sections
                key_file_match = self.config.has_option(section, "key_file")
                enabled = self.get_value(section, "enabled") == "1"
                # if found, check value is not empty
                if key_file_match and enabled:
                    self.get_value(section, "key_file")

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
