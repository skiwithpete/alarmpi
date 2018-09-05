#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

import alarmenv
import sound_the_alarm
import handlers


class AlarmEnvTestCase(unittest.TestCase):
    """Test cases for alarmenv: are properties read from the configuration file
    correctly?
    """

    @classmethod
    def setUpClass(self):
        test_config_file = "./tests/alarm_test.config"
        self.env = alarmenv.AlarmEnv(test_config_file)

    def testInvalidConfigFileRaisesError(self):
        """Does trying to create an AlarmEnv with a non-existing configuration file
        raise RuntimeError?
        """
        self.assertRaises(RuntimeError, alarmenv.AlarmEnv, "foo.config")

    def testValidateConfigRaisesErrorOnInvalid(self):
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

    def testValidateConfigPassesOnValid(self):
        """Does validate_config return True on valid config file."""
        res = self.env.validate_config()
        self.assertTrue(res)

    def testNoMatchOnInvalidConfigSection(self):
        """Does config_has_match return False on invalid section name?"""
        match = self.env.config_has_match("nosuchsection", "type", "foo")
        self.assertFalse(match)

    def testNoMatchOnInvalidConfigOption(self):
        """Does config_has_match return False on invalid option key?"""
        match = self.env.config_has_match("main", "nosuchoption", "foo")
        self.assertFalse(match)

    def testMatchOnValidConfigKeys(self):
        """Does config_has_match return True on valid section, option, key combination?"""
        match = self.env.config_has_match("greeting", "handler", "get_greeting.py")
        self.assertTrue(match)

    def testGetSectionsWithoutMain(self):
        """Does get_sections return section names without the main section"""
        names = ["greeting", "yahoo_weather", "BBC_news",
                 "google_translate_tts", "festival_tts", "radio"]
        read_sections = self.env.get_sections(True)
        self.assertEqual(names, read_sections)

    def testReadContentSections(self):
        """Does get_content_sections return correct section names?"""
        names = ["greeting", "yahoo_weather", "BBC_news"]
        read_sections = self.env.get_enabled_content_sections()
        self.assertEqual(names, read_sections)

        # disable a section and run again
        self.env.config["yahoo_weather"]["enabled"] = "0"
        read_sections = self.env.get_enabled_content_sections()
        names = ["greeting", "BBC_news"]
        self.assertEqual(names, read_sections)


class AlarmProcessingTestCase(unittest.TestCase):
    """Test cases for sound_the_alarm: is an alarm processed according
    to the configuration file?
    """

    @classmethod
    def setUpClass(self):
        test_config_file = "./tests/alarm_test.config"
        self.env = alarmenv.AlarmEnv(test_config_file)

    def testCorrectTTSClientChosen(self):
        """Does get_tts_client choose the first enabled TTS client?"""
        tts = sound_the_alarm.get_tts_client(self.env)
        self.assertIsInstance(tts, handlers.get_google_translate_tts.GoogleTranslateTTSManager)

    def testDefaultTTSClientChosenIfNoneSet(self):
        """Is the Festival client chosen when none is explicitly enaled?"""
        # disable all tts
        for section in self.env.config.sections():
            if section.lower().endswith("_tts"):
                self.env.config[section]["enabled"] = "0"

        tts = sound_the_alarm.get_tts_client(self.env)
        self.assertIsInstance(tts, handlers.get_festival_tts.FestivalTTSManager)

    def testCorrectHandlerCreated(self):
        """Is the correct class chosen for each content in the config file?"""
        greeting_class = sound_the_alarm.get_content_parser_class(self.env, "greeting")
        self.assertEqual(greeting_class, handlers.get_greeting.Greeting)

        weather_class = sound_the_alarm.get_content_parser_class(self.env, "yahoo_weather")
        self.assertEqual(weather_class, handlers.get_yahoo_weather.YahooWeatherClient)

        news_class = sound_the_alarm.get_content_parser_class(self.env, "BBC_news")
        self.assertEqual(news_class, handlers.get_bbc_news.NewsParser)


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmEnvTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(AlarmProcessingTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
