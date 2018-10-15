#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import unittest
from unittest import TestCase
from unittest.mock import patch

import alarmenv
import sound_the_alarm
import handlers


class AlarmProcessingTestCase(TestCase):
    """Test cases for sound_the_alarm: is an alarm processed according
    to the configuration file?
    """

    @classmethod
    def setUpClass(self):
        self.env = alarmenv.AlarmEnv("")

    @patch("alarmenv.AlarmEnv.get_value_with_fallback")
    @patch("sound_the_alarm.get_content_parser_class")
    @patch("alarmenv.AlarmEnv.get_enabled_sections")
    def test_correct_tts_client_chosen(self, mock_get_enabled_sections, mock_get_content_parser_class, mock_get_value_with_fallback):
        """Does get_tts_client choose the first enabled client?"""
        mock_get_enabled_sections.return_value = ["google_translate_tts"]

        from handlers import get_google_translate_tts
        mock_get_content_parser_class.return_value = get_google_translate_tts.GoogleTranslateTTSManager
        mock_get_value_with_fallback.return_value = None

        env = alarmenv.AlarmEnv("")
        client = sound_the_alarm.get_tts_client(env)
        self.assertIsInstance(client, get_google_translate_tts.GoogleTranslateTTSManager)

    @patch("alarmenv.AlarmEnv.get_enabled_sections")
    def test_default_TTS_client_chosen_when_none_set(self, mock_get_enabled_sections):
        """Is the Festival client chosen in get_tts_client when none is explicitly enaled?"""
        mock_get_enabled_sections.return_value = None

        from handlers import get_festival_tts
        env = alarmenv.AlarmEnv("")
        client = sound_the_alarm.get_tts_client(env)
        self.assertIsInstance(client, get_festival_tts.FestivalTTSManager)

    @patch("alarmenv.AlarmEnv.get_value")
    def test_correct_content_parser_chosen(self, mock_get_value):
        """Given a content section, is the correct class chosen in get_content_parser_class?"""
        #
        mock_get_value.side_effect = ["get_bbc_news.py", "get_festival_tts.py", "get_gcp_tts.py",
                                      "get_google_translate_tts.py", "get_greeting.py", "get_yahoo_weather.py"]

        # import handler modules
        from handlers import get_bbc_news, get_festival_tts, get_gcp_tts, get_google_translate_tts, get_greeting, get_yahoo_weather
        response_classes = [
            get_bbc_news.NewsParser,
            get_festival_tts.FestivalTTSManager,
            get_gcp_tts.GoogleCloudTTS,
            get_google_translate_tts.GoogleTranslateTTSManager,
            get_greeting.Greeting,
            get_yahoo_weather.YahooWeatherClient
        ]

        # run get_content_parser_class for each handler name and compare to the corresponding response_class
        for response_class in response_classes:
            env = alarmenv.AlarmEnv("")
            created_class = sound_the_alarm.get_content_parser_class(env, "")
            self.assertIs(created_class, response_class)

    @patch("sys.argv")
    @patch("pydub.playback.play")
    @patch("pydub.AudioSegment.from_mp3")
    def test_alarm_played_with_no_extra_sys_argv(self, mock_from_mp3, mock_play, mock_sys_argv):
        """Test the alarm is played when no path to the configuration file is provided
        as a command line argument to the script.
        """
        mock_sys_argv.return_value = []
        mock_from_mp3.return_value = "foo"
        sound_the_alarm.play_beep()
        mock_play.assert_called_with("foo")

    @patch("sys.argv")
    @patch("pydub.playback.play")
    @patch("pydub.AudioSegment.from_mp3")
    def test_alarm_sound_has_valid_file_path_when_sys_argv_provided(self, mock_from_mp3, mock_play, mock_sys_argv):
        """Test that a valid path to the alarm mp3 file is formed when a path to the configuration
        file is provided.
        """
        # use getcwd to format a path to an alarm.config file (need not exist for this test)
        mock_filepath = os.path.join(os.getcwd(), "sound_the_alarm.py")
        mock_sys_argv.return_value = ["/bin/python", mock_filepath]  # need 2 item in sys.argv

        base = os.path.dirname(mock_filepath)
        path = os.path.join(base, "resources", "Cool-alarm-tone-notification-sound.mp3")
        response_path = sound_the_alarm.play_beep()
        self.assertEqual(response_path, path)

    @patch("sound_the_alarm.play_beep")
    def test_beep_played_when_no_network(self, mock_play_beep):
        """Is the beep played when no network connection is detected?"""
        self.env.netup = False
        sound_the_alarm.main(self.env)
        mock_play_beep.assert_called()

    @patch("sound_the_alarm.play_beep")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_beep_played_when_no_readaloud(self, mock_config_has_match, mock_play_beep):
        """Is the beep played when readaloud = 0 is set in the configuration?"""
        self.env.netup = True
        mock_config_has_match.return_value = False
        sound_the_alarm.main(self.env)
        mock_play_beep.assert_called()

    @patch("sound_the_alarm.play_radio")
    @patch("sound_the_alarm.play_beep")
    @patch("alarmenv.AlarmEnv.config_has_match")
    def test_radio_played_when_enabled(self, mock_config_has_match, mock_play_beep, mock_play_radio):
        """Is a radio stream opened when radio is enabled in the config?"""
        mock_config_has_match.side_effect = [False, True]  # skip the tts check
        sound_the_alarm.main(self.env)
        mock_play_radio.assert_called()


class HandlerTestCase(TestCase):
    """Test cases for content handlers."""

    def test_sunset_time_formatted_with_double_minute_digits(self):
        """Are sunset & sunrise timestring returned by the weather API correctly formatted
        with double digit minute readings?
        """
        from handlers import get_yahoo_weather

        formatted = get_yahoo_weather.YahooWeatherClient.format_time_string("8:3 am")
        self.assertEqual(formatted, "08:03 AM")


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmProcessingTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(HandlerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
