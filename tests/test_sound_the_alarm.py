#!/usr/bin/python
# -*- coding: utf-8 -*-


import unittest
from unittest import TestCase
from unittest.mock import patch

import alarmenv
import alarm_builder
import handlers.get_bbc_news
import handlers.get_festival_tts
import handlers.get_gcp_tts
import handlers.get_google_translate_tts
import handlers.get_greeting
import handlers.get_open_weather


class AlarmProcessingTestCase(TestCase):
    """Test cases for alarm_builder: is an alarm processed according
    to the configuration file?
    """

    def setUp(self):
        """Create an Alarm object using a dummy AlarmEnv."""
        env = alarmenv.AlarmEnv("mock_config_file")
        self.alarm = alarm_builder.Alarm(env)
        self.alarm.env.radio_url = False

    @patch("alarmenv.AlarmEnv.get_value")
    @patch("alarm_builder.Alarm.get_content_parser_class")
    @patch("alarmenv.AlarmEnv.get_enabled_sections")
    def test_first_enabled_tts_client_chosen(self, mock_get_enabled_sections, mock_get_content_parser_class, mock_get_value):
        """Does get_tts_client choose the first enabled client?"""
        mock_get_enabled_sections.return_value = ["google_translate_tts"]

        mock_get_content_parser_class.return_value = handlers.get_google_translate_tts.GoogleTranslateTTSManager
        mock_get_value.return_value = None

        client = self.alarm.get_tts_client()
        self.assertIsInstance(client, handlers.get_google_translate_tts.GoogleTranslateTTSManager)

    @patch("alarmenv.AlarmEnv.get_enabled_sections")
    def test_default_TTS_client_chosen_when_none_set(self, mock_get_enabled_sections):
        """Is the Festival client chosen in get_tts_client when none is explicitly enaled?"""
        mock_get_enabled_sections.return_value = None

        client = self.alarm.get_tts_client()
        self.assertIsInstance(client, handlers.get_festival_tts.FestivalTTSManager)

    @patch("alarmenv.AlarmEnv.get_value")
    def test_correct_content_parser_chosen(self, mock_get_value):
        """Given a content section, is the correct class chosen in get_content_parser_class?"""
        mock_get_value.side_effect = ["get_bbc_news.py", "get_festival_tts.py", "get_gcp_tts.py",
                                      "get_google_translate_tts.py", "get_greeting.py", "get_open_weather.py"]

        # import handler modules
        response_classes = [
            handlers.get_bbc_news.NewsParser,
            handlers.get_festival_tts.FestivalTTSManager,
            handlers.get_gcp_tts.GoogleCloudTTS,
            handlers.get_google_translate_tts.GoogleTranslateTTSManager,
            handlers.get_greeting.Greeting,
            handlers.get_open_weather.OpenWeatherMapClient
        ]

        # run get_content_parser_class for each handler name and compare to the corresponding response_class
        for response_class in response_classes:
            created_class = self.alarm.get_content_parser_class("")
            self.assertIs(created_class, response_class)

    @patch("alarm_builder.Alarm.play_beep")
    @patch("alarm_builder.Alarm.gui_running")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_beep_played_when_no_network(self, mock_config_has_match, mock_gui_running, mock_play_beep):
        """Is the beep played when no network connection is detected?"""
        mock_gui_running.return_value = False
        mock_config_has_match.return_value = True  # is GUI running
        self.alarm.env.netup = False
        self.alarm.main()

        mock_play_beep.assert_called()

    @patch("alarm_builder.Alarm.play_beep")
    @patch("alarm_builder.Alarm.gui_running")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_beep_played_when_no_readaloud(self, mock_config_has_match, mock_gui_running, mock_play_beep):
        """Is the beep played when readaloud = 0 is set in the configuration?"""
        mock_gui_running.return_value = False
        mock_config_has_match.return_value = False  # is GUI running
        self.alarm.env.netup = True
        self.alarm.main()

        mock_play_beep.assert_called()

    @patch("alarm_builder.Alarm.play_radio")
    @patch("alarm_builder.Alarm.get_tts_client")
    @patch("alarm_builder.Alarm.generate_content")
    @patch("alarm_builder.Alarm.gui_running")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_radio_played_when_enabled(self, mock_config_has_match, mock_gui_running, mock_generate_content, mock_get_tts_client, mock_play_radio):
        """Is a radio stream opened when radio is enabled in the config?"""
        mock_gui_running.return_value = False
        mock_config_has_match.return_value = True  # is GUI running

        self.alarm.env.netup = True
        self.alarm.env.radio_url = True

        self.alarm.main()
        mock_play_radio.assert_called()


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmProcessingTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
