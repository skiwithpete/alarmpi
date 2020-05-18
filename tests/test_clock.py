#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os.path
import unittest
from unittest import TestCase
from unittest.mock import (patch, Mock)
from PyQt5.QtWidgets import QApplication

import src
from src import clock



class ClockTestCase(TestCase):
    """Test cases for logic functions for determining alarm time in Clock."""

    @patch("src.alarmenv.AlarmEnv.get_config_file_path")
    def setUp(self, mock_get_config_file_path):
        app = QApplication([]) # Setup a dummy QApplication to be able to create widgets (return value is needed to prevent garbage collection?)

        mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")
        self.clock = clock.Clock("dummy.conf")
        self.clock.setup()

    @patch("src.GUIWidgets.SettingsWindow.validate_alarm_input")
    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    def test_set_alarm_updates_screen_and_sets_timers(self, mock_display, mock_validate_alarm_input):
        """Does 'Set alarm' button start timers for alarm build and play and update
        main window and settings window labels?
        """
        mock_validate_alarm_input.return_value = "00:10"  # Mock validating a not-set alarm time

        self.clock.settings_window.numpad_buttons["set"].click()
        self.assertTrue(self.clock.alarm_timer.isActive())
        self.assertTrue(self.clock.alarm_build_timer.isActive())
        
        mock_display.assert_called_with("00:10")

        settings_window_value = self.clock.settings_window.alarm_time_status_label.text()
        self.assertEqual(settings_window_value, "Alarm set for 00:10")
  
    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    def test_clear_alarm_clears_screen_and_stops_timers(self, mock_display):
        """Does 'Clearm alarm' button stop timers for alarm build and play and clear
        main window and settings window labels?
        """
        self.clock.settings_window.numpad_buttons["clear"].click()
        self.assertFalse(self.clock.alarm_timer.isActive())
        self.assertFalse(self.clock.alarm_build_timer.isActive())
        
        mock_display.assert_called_with("")

        settings_window_value = self.clock.settings_window.alarm_time_status_label.text()
        self.assertEqual(settings_window_value, "Alarm cleared")

    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    @patch("src.rpi_utils.set_display_backlight_brightness")
    def test_play_alarm_starts_alarm_play_thread(self, mock_set_display_backlight_brightness, mock_display):
        """Does the timer slot function for playing the alarm set window brightness,
        clearn main window label and start the alarm play thread?
        """
        self.clock.alarm_play_thread.start = Mock()
        self.clock.enable_screen_and_show_control_buttons = Mock()

        self.clock.play_alarm()
        mock_display.assert_called_with("")
        mock_set_display_backlight_brightness.assert_called_with(255)
        self.clock.alarm_play_thread.start.assert_called()

    def test_finish_playing_alarm_starts_radio_if_enabled(self):
        """Does the alarm finish callback call the radio thread when radio is enabled?"""
        self.clock.env.config.set("radio", "enabled", "1")
        self.clock.main_window.control_buttons["Radio"] = Mock()

        self.clock.finish_playing_alarm()
        self.clock.main_window.control_buttons["Radio"].click.assert_called()


class RadioStreamerTestCase(TestCase):
    """Test cases for RadioStreamer: does streaming radio work correctly?"""

    def setUp(self):
        self.radio = clock.RadioStreamer("dummy_args")

    def test_radio_not_playing_on_empty_process(self):
        """Does is_playing return False when there active process flag is not set?"""
        self.radio.process = None
        res = self.radio.is_playing()
        self.assertFalse(res)

    def test_radio_is_playing_on_non_empty_process(self):
        """Does is_playing return True when an active process flag is set?"""
        self.radio.process = True
        res = self.radio.is_playing()
        self.assertTrue(res)

    @patch("subprocess.Popen")
    def test_stop_clears_active_process(self, mock_Popen):
        """Does stop clear the list of running processes?"""
        self.radio.play()
        self.radio.stop()

        self.assertEqual(self.radio.process, None)



if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(ClockTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(RadioStreamerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
