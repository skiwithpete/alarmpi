# Wrapper class for reading alarm configuration file.

import logging
import os
import yaml

import requests
from src import utils, rpi_utils


logger = logging.getLogger("eventLogger")


class AlarmConfig:
    """Parses the configuration file to a readable object."""

    def __init__(self, config_file):
        """Setup an absolute path to the configuration file and a parser.
        params
            config_file (str): name (not path!) of the configuration file to use.
        """
        self.config_file = config_file
        self.path_to_config = self.get_config_file_path()
        with open(self.path_to_config) as f:
            self.config = yaml.safe_load(f)

        self.validate()

        # Check for write access to Raspberry Pi system backlight brightness files
        self.rpi_brightness_write_access = all([os.access(p, os.W_OK) for p in [
            rpi_utils.BRIGHTNESS_FILE, rpi_utils.POWER_FILE]]
        )

    def __getitem__(self, item):
        # Make the object subscriptable for convenience
        return self.config[item]

    def get_config_file_path(self):
        """Given a filename, look for an alarm configuration file from either:
          * $HOME/.alarmpi, or
          * BASE/configs
        Return:
            path to first detected config file or None is none found
        """
        PATHS_TO_CHECK = [
            os.path.expanduser("~/.alarmpi/" + self.config_file),
            os.path.join(utils.BASE, "configs", self.config_file)
        ]

        for path in PATHS_TO_CHECK:
            if os.path.isfile(path):
                normalized_path = os.path.normpath(path)
                logger.info("Using config file %s", normalized_path)
                return normalized_path

        raise FileNotFoundError("No valid configuration file found for {}".format(self.config_file))

    def _testnet(self):
        # Test for connectivity
        host = "http://www.google.com"
        try:
            requests.get(host)
            return True
        except requests.RequestException:
            logger.warning("Could not resolve '%s'. Assuming the network is down.", host)
            return False

    def validate(self):
        """Validate configuration file: checks that
         * low_brightness value is valid
         * default radio station is valid 
         * content and TTS sections have 'handler' key
         * at most 1 TTS engine is enabled
        """

        for item in self["content"]:
            assert "handler" in self["content"][item], "Missing handler from content" + item

        for item in self["TTS"]:
            assert "handler" in self["TTS"][item], "Missing handler from TTS" + item

        n_tts_enabled = len([self["TTS"][item]["enabled"] for item in self["TTS"] if self["TTS"][item]["enabled"]])
        assert n_tts_enabled == 1, "Multiple TTS engines enabled"

        brightness = self["main"]["low_brightness"]
        assert 9 <= brightness <= 255, "Invalid configuration: Brightness should be between 9 and 255"

        default = self["radio"]["default"]
        assert default in self["radio"]["urls"], "No stream url for defult radio station" + default

        return True

    def get_enabled_sections(self, type):
        """Return names of sections sections whose 'type' is section_type (either 'content' or 'tts')."""
        return {k:v for k,v in self[type].items() if self[type][k].get("enabled")}
