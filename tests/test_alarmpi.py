#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase
from unittest.mock import patch
from unittest.mock import MagicMock

import alarmenv
import sound_the_alarm
import handlers


def print_foo():
    return "foo"


class AlarmEnvTestCase(TestCase):
    """Test cases for alarmenv: are properties read from the configuration file
    correctly?
    """

    @classmethod
    def setUpClass(self):
        test_config_file = "./tests/alarm_test.config"
        self.env = alarmenv.AlarmEnv(test_config_file)

    def test_invalid_config_file_raises_error(self):
        """Does trying to create an AlarmEnv with a non-existing configuration file
        raise RuntimeError?
        """
        self.assertRaises(RuntimeError, alarmenv.AlarmEnv, "foo.config")

    def test_validate_config_raises_error_on_invalid(self):
        """Does validate_config raise RuntimeError on
            1 missing 'type' key,
            2 missing handler for content section
        """
        # create a new AlarmEnv and remove enabled key
        env = alarmenv.AlarmEnv("./tests/alarm_test.config")
        del env.config["yahoo_weather"]["enabled"]
        self.assertRaises(RuntimeError, env.validate_config)

        # create a new AlarmEnv and remove type key
        env = alarmenv.AlarmEnv("./tests/alarm_test.config")
        del env.config["yahoo_weather"]["type"]
        self.assertRaises(RuntimeError, env.validate_config)

    @unittest.skip("broken")
    def test_mock_validate_config_raises_error_on_invalid(self):
        """Does validate_config raise RuntimeError on
            1 missing 'type' key,
            2 missing handler for content section
        """
        # create a new AlarmEnv and remove enabled key
        mock_config_file = MagicMock()
        env = alarmenv.AlarmEnv(mock_config_file)
        env = MagicMock(name="mock_env")

        del env.config["yahoo_weather"]["enabled"]
        self.assertRaises(RuntimeError, env.validate_config)

        # create a new AlarmEnv and remove type key
        env = alarmenv.AlarmEnv("./tests/alarm_test.config")
        del env.config["yahoo_weather"]["type"]
        self.assertRaises(RuntimeError, env.validate_config)

    def test_validate_config_passes_on_valid(self):
        """Does validate_config return True on valid config file."""
        res = self.env.validate_config()
        self.assertTrue(res)

    def test_no_match_on_invalid_config_section(self):
        """Does config_has_match return False on invalid section name?"""
        match = self.env.config_has_match("nosuchsection", "type", "foo")
        self.assertFalse(match)

    def test_no_match_on_invalid_config_option(self):
        """Does config_has_match return False on invalid option key?"""
        match = self.env.config_has_match("main", "nosuchoption", "foo")
        self.assertFalse(match)

    def test_match_on_valid_config_keys(self):
        """Does config_has_match return True on valid section, option, key combination?"""
        match = self.env.config_has_match("greeting", "handler", "get_greeting.py")
        self.assertTrue(match)

    def test_get_sections_without_main(self):
        """Does get_sections return section names without the main section"""
        names = ["greeting", "yahoo_weather", "BBC_news", "google_gcp_tts",
                 "google_translate_tts", "festival_tts", "radio"]
        read_sections = self.env.get_sections(True)
        self.assertEqual(names, read_sections)

    def test_read_content_sections(self):
        """Does get_content_sections return correct section names?"""
        names = ["greeting", "yahoo_weather", "BBC_news"]
        read_sections = self.env.get_enabled_content_sections()
        self.assertEqual(names, read_sections)

        # disable a section and run again
        self.env.config["yahoo_weather"]["enabled"] = "0"
        read_sections = self.env.get_enabled_content_sections()
        names = ["greeting", "BBC_news"]
        self.assertEqual(names, read_sections)


class AlarmProcessingTestCase(TestCase):
    """Test cases for sound_the_alarm: is an alarm processed according
    to the configuration file?
    """

    @classmethod
    def setUpClass(self):
        test_config_file = "./tests/alarm_test.config"
        self.env = alarmenv.AlarmEnv(test_config_file)

    def test_first_TTS_client_chosen(self):
        """Does get_tts_client choose the first enabled TTS client?"""
        tts = sound_the_alarm.get_tts_client(self.env)
        self.assertIsInstance(tts, handlers.get_gcp_tts.GoogleCloudTTS)

    def test_default_TTS_client_chosen_when_none_set(self):
        """Is the Festival client chosen when none is explicitly enaled?"""
        # disable all tts
        for section in self.env.config.sections():
            if section.lower().endswith("_tts"):
                self.env.config[section]["enabled"] = "0"

        tts = sound_the_alarm.get_tts_client(self.env)
        self.assertIsInstance(tts, handlers.get_festival_tts.FestivalTTSManager)

        # re-enable for other tests to not fail because of disabled status
        for section in self.env.config.sections():
            if section.lower().endswith("_tts"):
                self.env.config[section]["enabled"] = "1"

    def test_correct_handler_created(self):
        """Is the correct class chosen for each content in the config file?"""
        greeting_class = sound_the_alarm.get_content_parser_class(self.env, "greeting")
        self.assertEqual(greeting_class, handlers.get_greeting.Greeting)

        weather_class = sound_the_alarm.get_content_parser_class(self.env, "yahoo_weather")
        self.assertEqual(weather_class, handlers.get_yahoo_weather.YahooWeatherClient)

        news_class = sound_the_alarm.get_content_parser_class(self.env, "BBC_news")
        self.assertEqual(news_class, handlers.get_bbc_news.NewsParser)

    @patch("sound_the_alarm.play_radio")
    @patch("sound_the_alarm.play_beep")
    def test_beep_played_when_no_readaloud(self, mock_play_beep, mock_play_radio):
        """Is the beep played when no network connection is detected?"""
        self.env.config["main"]["readaloud"] = "0"
        sound_the_alarm.main(self.env)
        mock_play_beep.assert_called()
        self.env.config["main"]["readaloud"] = "1"

    @patch("sound_the_alarm.play_beep")
    def test_beep_played_when_no_network_connection(self, mock_play_beep):
        """Is the beep played when readaloud=0 is set in the configuration"""
        self.env.netup = False
        sound_the_alarm.main(self.env)
        mock_play_beep.assert_called()
        self.env.netup = True

    @patch('sound_the_alarm.main', side_effect=print_foo)
    def test_print_foo(self, main):
        res = main()
        self.assertEqual(res, "foo")


class HandlerTestCases(TestCase):
    """Test cases for content handlers."""

    @classmethod
    def setUpClass(self):
        test_config_file = "./tests/alarm_test.config"
        self.env = alarmenv.AlarmEnv(test_config_file)

    def test_sunset_time_formatted_with_double_minute_digits(self):
        """Is weather API returned sunset & sunrise timestring correctly formatted
        with double digit minute reading.
        """
        section_data = self.env.get_section("yahoo_weather")
        weather_client = handlers.get_yahoo_weather.YahooWeatherClient(section_data)
        formatted = weather_client.format_time_string("8:3 am")
        self.assertEqual(formatted, "08:03 AM")


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmEnvTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmProcessingTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(HandlerTestCases)
    unittest.TextTestRunner(verbosity=2).run(suite)
