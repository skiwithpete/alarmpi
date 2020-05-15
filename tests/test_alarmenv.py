#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import configparser
import unittest
from unittest import TestCase
from unittest.mock import patch

from src import alarmenv


class AlarmEnvTestCase(TestCase):
    """Test cases for alarmenv: are properties read from the configuration file
    correctly?
    """

    @patch("src.alarmenv.AlarmEnv.get_config_file_path")
    def setUp(self, mock_get_config_file_path):
        mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")
        self.env = alarmenv.AlarmEnv("dummy_config_name")
        self.env.setup()

    @patch("src.alarmenv.AlarmEnv.get_sections")
    def test_validate_config_raises_runtime_error_on_invalid(self, mock_get_sections):
        """Does validate_config raise RuntimeError when configparser detects invalid
        options?
        """
        mock_get_sections.side_effect = configparser.NoSectionError("")
        self.assertRaises(RuntimeError, self.env.validate_config)

    @patch("src.alarmenv.AlarmEnv.get_config_file_path")
    def test_invalid_config_file_raises_error(self, mock_get_config_file_path):
        """Does trying to create an AlarmEnv with a non-existing configuration file
        raise RuntimeError?
        """
        # Create a new AlarmEnv with a non-existing parameter but point to the existing configuration
        # to avoid FileNotFoundError in get_config_file_path.
        mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")
        env = alarmenv.AlarmEnv("dummy.conf")
        env.config_file = "dummy.conf"  # config_file attribute is set to existing test file, manually change back to dummy file before calling setup
        self.assertRaises(RuntimeError, env.setup)

    def test_no_match_on_invalid_config_section(self):
        """Does config_has_match return False (instead of an Exception) when checking for invalid section?"""
        match = self.env.config_has_match("invalidsection", "enabled", "1")
        self.assertFalse(match)

    def test_match_on_valid_config_keys(self):
        """Does config_has_match return True on valid section, option, key combination?"""
        match = self.env.config_has_match("BBC_news", "enabled", "1")
        self.assertTrue(match)

    def test_get_sections_with_exclusions(self):
        """Does get_sections return correct section names when called with exclusions?"""
        read_sections = self.env.get_sections(excludes=["main", "greeting"])

        filtered_sections = ["alarm", "polling", "openweathermap", "BBC_news", "google_gcp_tts",
                             "google_translate_tts", "festival_tts", "radio"]
        self.assertCountEqual(read_sections, filtered_sections)  # note: checks for same elements as well counts

    def test_read_content_sections(self):
        """Does get_enabled_sections return correct content section names?"""
        sections = self.env.get_enabled_sections("content")
        self.assertEqual(sections, ["BBC_news"])


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmEnvTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
