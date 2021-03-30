import logging
import os
import json
import configparser
import dns.resolver
import dns.exception

from src import utils, rpi_utils


logger = logging.getLogger("eventLogger")

class AlarmEnv:
    """Parses the configuration file to a readable object."""

    def __init__(self, config_file):
        """Setup an absolute path to the configuration file and a parser.
        params
            config_file (str): name (not path!) of the configuration file to use.
        """
        path_to_config = self.get_config_file_path(config_file)

        self.config_file = path_to_config
        self.config = configparser.ConfigParser()

        # Check for write access to Raspberry Pi system backlight brightness files
        self.rpi_brightness_write_access = all([os.access(p, os.W_OK) for p in [rpi_utils.BRIGHTNESS_FILE, rpi_utils.POWER_FILE]])
        
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
                normalized_path = os.path.normpath(path)
                logger.info("Using config file %s", normalized_path)
                return normalized_path

        raise FileNotFoundError("No valid configuration file found for {}".format(config_file))

    def _testnet(self):
        # Test for connectivity
        nthost = "translate.google.com"
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
        """
        try:
            for section in self.get_sections(excludes=["main", "alarm", "plugins", "greeting"]):
                section_type = self.get_value(section, "type")

                if section_type in ("content", "tts"):
                    self.get_value(section, "handler")  # raises NoOptionError if no 'handler' key
                    self.get_value(section, "enabled")

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise RuntimeError("Invalid configuration: ", e)

        brightness = int(self.get_value("main", "low_brightness", "12"))
        if not 9 <= brightness <= 255:
            raise RuntimeError("Invalid configuration: Brightness should be between 9 and 255")

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
        return self.config[section]

    def get_value(self, section, option, fallback=None):
        """Get a value matching a section and option. Raises either NoSectionError or
        NoOptionError on invalid input.
        """
        if fallback is None:
            return self.config.get(section, option)

        return self.config.get(section, option, fallback=fallback)

    def get_radio_stations(self):
        """Utility function for parsing radio stream urls as a dict."""
        return json.loads(self.get_value("radio", "urls"))