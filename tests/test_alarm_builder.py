#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import unittest
from unittest import TestCase
from unittest.mock import patch

from src import alarmenv
from src import alarm_builder
from src.handlers import get_google_translate_tts
from src.handlers import get_festival_tts
from src.handlers import get_bbc_news
from src.handlers import get_gcp_tts
from src.handlers import get_greeting
from src.handlers import get_open_weather


class AlarmProcessingTestCase(TestCase):
    """Test cases for alarm_builder: is an alarm processed according
    to the configuration file?
    """

    @patch("src.alarmenv.AlarmEnv.get_config_file_path")
    def setUp(self, mock_get_config_file_path):
        """Create an AlarmEnv using test_alarm.conf."""
        mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")
        env = alarmenv.AlarmEnv("dummy_config_name") # name will be ignored, above path will be used instead
        env.setup() # parse the configuration (also validates it, no need to mock)
        self.alarm = alarm_builder.Alarm(env)

    def test_first_enabled_tts_client_chosen(self):
        """Does get_tts_client choose the first enabled client?"""
        self.alarm.env.config.set("google_gcp_tts", "enabled", "0")
        self.alarm.env.config.set("google_translate_tts", "enabled", "1")
        self.alarm.env.config.set("festival_tts", "enabled", "0")

        client = self.alarm.get_tts_client()
        self.assertIsInstance(
            client, get_google_translate_tts.GoogleTranslateTTSManager)

    def test_default_TTS_client_chosen_when_none_set(self):
        """Is the Festival client chosen in get_tts_client when none is explicitly enaled?"""
        self.alarm.env.config.set("google_gcp_tts", "enabled", "0")
        self.alarm.env.config.set("google_translate_tts", "enabled", "0")
        self.alarm.env.config.set("festival_tts", "enabled", "0")

        client = self.alarm.get_tts_client()
        self.assertIsInstance(client, get_festival_tts.FestivalTTSManager)

    @patch("src.alarmenv.AlarmEnv.get_value")
    def test_correct_content_parser_chosen(self, mock_get_value):
        """Given a content section, is the correct class chosen in get_content_parser_class?"""
        mock_get_value.side_effect = ["get_bbc_news.py", "get_festival_tts.py", "get_gcp_tts.py",
                                      "get_google_translate_tts.py", "get_greeting.py", "get_open_weather.py"]

        # import handler modules
        response_classes = [
            get_bbc_news.NewsParser,
            get_festival_tts.FestivalTTSManager,
            get_gcp_tts.GoogleCloudTTS,
            get_google_translate_tts.GoogleTranslateTTSManager,
            get_greeting.Greeting,
            get_open_weather.OpenWeatherMapClient
        ]

        # run get_content_parser_class for each handler name and compare to the corresponding response_class
        for response_class in response_classes:
            created_class = self.alarm.get_content_parser_class("dummy_section")
            self.assertIs(created_class, response_class)

    @patch("src.alarmenv.AlarmEnv._testnet")
    @patch("src.alarm_builder.Alarm.play_beep")
    def test_beep_played_when_no_network(self, mock_play_beep, mock_testnet):
        """Is the beep played when no network connection is detected?"""
        mock_testnet.return_value = False

        self.alarm.play("dummy_content")
        mock_play_beep.assert_called()


    @patch("src.alarmenv.AlarmEnv.config_has_match")
    @patch("src.alarm_builder.Alarm.play_beep")
    def test_beep_played_when_no_readaloud(self, mock_play_beep, mock_config_has_match):
        """Is the beep played when readaloud = 0 is set in the configuration?"""
        mock_config_has_match.return_value = False  # mock TTS detection call

        self.alarm.play("dummy_content")
        mock_play_beep.assert_called()


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmProcessingTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
