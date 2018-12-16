#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import unittest
from unittest import TestCase
from unittest.mock import patch

import sound_the_alarm
import handlers.get_bbc_news
import handlers.get_festival_tts
import handlers.get_gcp_tts
import handlers.get_google_translate_tts
import handlers.get_greeting
import handlers.get_yahoo_weather


class AlarmProcessingTestCase(TestCase):
    """Test cases for sound_the_alarm: is an alarm processed according
    to the configuration file?
    """

    @patch("alarmenv.AlarmEnv.setup")
    def setUp(self, mock_setup):
        self.alarm = sound_the_alarm.Alarm("")
        self.alarm.env.radio_url = False

    @patch("alarmenv.AlarmEnv.get_value_with_fallback")
    @patch("sound_the_alarm.Alarm.get_content_parser_class")
    @patch("alarmenv.AlarmEnv.get_enabled_sections")
    def test_correct_tts_client_chosen(self, mock_get_enabled_sections, mock_get_content_parser_class, mock_get_value_with_fallback):
        """Does get_tts_client choose the first enabled client?"""
        mock_get_enabled_sections.return_value = ["google_translate_tts"]

        mock_get_content_parser_class.return_value = handlers.get_google_translate_tts.GoogleTranslateTTSManager
        mock_get_value_with_fallback.return_value = None

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
        #
        mock_get_value.side_effect = ["get_bbc_news.py", "get_festival_tts.py", "get_gcp_tts.py",
                                      "get_google_translate_tts.py", "get_greeting.py", "get_yahoo_weather.py"]

        # import handler modules
        response_classes = [
            handlers.get_bbc_news.NewsParser,
            handlers.get_festival_tts.FestivalTTSManager,
            handlers.get_gcp_tts.GoogleCloudTTS,
            handlers.get_google_translate_tts.GoogleTranslateTTSManager,
            handlers.get_greeting.Greeting,
            handlers.get_yahoo_weather.YahooWeatherClient
        ]

        # run get_content_parser_class for each handler name and compare to the corresponding response_class
        for response_class in response_classes:
            created_class = self.alarm.get_content_parser_class("")
            self.assertIs(created_class, response_class)

    @patch("sound_the_alarm.Alarm.play_beep")
    def test_beep_played_when_no_network(self, mock_play_beep):
        """Is the beep played when no network connection is detected?"""
        self.alarm.env.netup = False
        self.alarm.main()
        mock_play_beep.assert_called()

    @patch("sound_the_alarm.Alarm.play_beep")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_beep_played_when_no_readaloud(self, mock_config_has_match, mock_play_beep):
        """Is the beep played when readaloud = 0 is set in the configuration?"""
        self.alarm.env.netup = True
        mock_config_has_match.return_value = False
        self.alarm.main()
        mock_play_beep.assert_called()

    @patch("sound_the_alarm.Alarm.play_radio")
    @patch("sound_the_alarm.Alarm.play")
    @patch("sound_the_alarm.Alarm.generate_content")
    @patch("sound_the_alarm.Alarm.gui_running")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_radio_played_when_enabled(self, mock_config_has_match, mock_gui_running, mock_generate_content, mock_play, mock_play_radio):
        """Is a radio stream opened when radio is enabled in the config?"""
        mock_gui_running.return_value = False
        mock_config_has_match.return_value = True
        mock_generate_content.return_value = "dummy content"  # need non empty content

        self.alarm.env.netup = True
        self.alarm.env.radio_url = True

        self.alarm.main()
        mock_play_radio.assert_called()

    @patch("sound_the_alarm.Alarm.play")
    @patch("sound_the_alarm.Alarm.gui_running")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_wakeup_signal_sent_if_gui_running(self, mock_config_has_match, mock_gui_running, mock_play):
        """Is a SIGUSR2 signal sent to the GUI process if determined to be running?"""
        mock_gui_running.return_value = 125
        mock_config_has_match.return_value = True

        self.alarm.env.netup = False

        self.alarm.main()
        mock_play.assert_called_with(sound_the_alarm.Alarm.play_beep, pid=125)


class HandlerTestCase(TestCase):
    """Test cases for content handlers."""

    def test_sunset_time_formatted_with_double_minute_digits(self):
        """Are sunset & sunrise timestring returned by the weather API correctly formatted
        with double digit minute readings?
        """
        formatted = handlers.get_yahoo_weather.YahooWeatherClient.format_time_string("8:3 am")
        self.assertEqual(formatted, "08:03 AM")


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmProcessingTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(HandlerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
