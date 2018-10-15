#!/usr/bin/python
# -*- coding: utf-8 -*-

import configparser
import unittest
from unittest import TestCase
from unittest.mock import patch

import alarmenv


class AlarmEnvTestCase(TestCase):
    """Test cases for alarmenv: are properties read from the configuration file
    correctly?
    """

    def setUp(self):
        self.env = alarmenv.AlarmEnv("")

    @patch("alarmenv.AlarmEnv.get_sections")
    def test_validate_config_raises_runtime_error_on_invalid(self, mock_get_sections):
        """Does validate_config raise RuntimeError when configparser detects invalid
        options?
        """
        mock_get_sections.side_effect = configparser.NoSectionError("foo")
        self.assertRaises(RuntimeError, self.env.validate_config)

    def test_invalid_config_file_raises_error(self):
        """Does trying to create an AlarmEnv with a non-existing configuration file
        raise RuntimeError?
        """
        env = alarmenv.AlarmEnv("foo.config")  # create a new AlarmEnv with non-existing file
        self.assertRaises(RuntimeError, env.setup)

    @patch("alarmenv.AlarmEnv.get_value")
    def test_no_match_on_invalid_config_section(self, mock_get_value):
        """Does config_has_match return False on invalid section name?"""
        mock_get_value.return_value = "mock_response"

        match = self.env.config_has_match("nosuchsection", "type", "value")
        self.assertFalse(match)

    @patch("alarmenv.AlarmEnv.get_value")
    def test_match_on_valid_config_keys(self, mock_get_value):
        """Does config_has_match return True on valid section, option, key combination?"""
        mock_get_value.return_value = "value"

        match = self.env.config_has_match("section", "option", "value")
        self.assertTrue(match)

    @patch("configparser.ConfigParser.sections")
    def test_get_sections_without_main(self, mock_sections):
        """Does get_sections return section names without the main section?"""
        mock_sections.return_value = ["main", "greeting", "yahoo_weather", "BBC_news", "google_gcp_tts",
                                      "google_translate_tts", "festival_tts", "radio"]
        read_sections = self.env.get_sections(True)

        filtered_sections = ["greeting", "yahoo_weather", "BBC_news", "google_gcp_tts",
                             "google_translate_tts", "festival_tts", "radio"]
        self.assertEqual(read_sections, filtered_sections)

    @patch("alarmenv.AlarmEnv.config_has_match")
    @patch("alarmenv.AlarmEnv.get_sections")
    def test_read_content_sections(self, mock_get_sections, mock_config_has_match):
        """Does get_enabled_type_sections return correct content section names?"""
        mock_get_sections.return_value = ["greeting", "yahoo_weather", "BBC_news"]
        # sets the first 2 items as 'enabled'
        mock_config_has_match.side_effect = [True, True, True, True, False, False]

        sections = self.env.get_enabled_sections("content")
        self.assertEqual(sections, ["greeting", "yahoo_weather"])


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmEnvTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
