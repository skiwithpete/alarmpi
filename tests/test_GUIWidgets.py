#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import unittest
from unittest import TestCase
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication

from src import clock, GUIWidgets, alarmenv




class ClockGUITestCase(TestCase):
    """Test cases for logic functions in GUIWidgets"""

    @patch("src.alarmenv.AlarmEnv.get_config_file_path")
    def setUp(self, mock_get_config_file_path):
        app = QApplication([]) # Setup a dummy QApplication to be able to create widgets (return value is needed to prevent garbage collection?)

        mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")
        ex = clock.Clock("dummy.conf")
        ex.setup()

        self.settings_window = GUIWidgets.SettingsWindow()
        self.main_window = GUIWidgets.AlarmWindow()

    def test_hour_update_alarm_display_time(self):
        """Does update_input_alarm_display write the correct time value to the
        settings window's set alarm time label?
        """
        # update when label is initially empty
        self.settings_window.input_alarm_time_label.setText(
            GUIWidgets.SettingsWindow.ALARM_LABEL_EMPTY)
        self.settings_window.update_input_alarm_display("0")
        val = self.settings_window.input_alarm_time_label.text()
        self.assertEqual(val, "0 :  ")

        # add second digit
        self.settings_window.update_input_alarm_display("7")
        val = self.settings_window.input_alarm_time_label.text()
        self.assertEqual(val, "07:  ")

        self.settings_window.update_input_alarm_display("1")
        val = self.settings_window.input_alarm_time_label.text()
        self.assertEqual(val, "07:1 ")

        self.settings_window.update_input_alarm_display("8")
        val = self.settings_window.input_alarm_time_label.text()
        self.assertEqual(val, "07:18")

        # 5th call should start from the beginning
        self.settings_window.update_input_alarm_display("1")
        val = self.settings_window.input_alarm_time_label.text()
        self.assertEqual(val, "1 :  ")

    def test_validate_alarm_input_rejects_invalid_input(self):
        """Does validate_alarm_input reject invalid input format and set user
        information labels accordingly.
        """
        # set the label to an invalid value and call the method
        self.settings_window.input_alarm_time_label.setText("25:01")
        self.settings_window.validate_alarm_input()

        # check labels contain expected error values
        error_value = self.settings_window.alarm_time_error_label.text()
        alarm_time_value = self.settings_window.input_alarm_time_label.text()

        self.assertEqual(error_value, "ERROR: Invalid time")
        self.assertEqual(alarm_time_value, "  :  ")

    def test_validate_alarm_input_returns_valid_input(self):
        """Does validate_alarm_input reject invalid input format and set user
        information labels accordingly.
        """
        # set the label to an invalid value and call the method
        self.settings_window.input_alarm_time_label.setText("16:34")
        val = self.settings_window.validate_alarm_input()
        self.assertEqual(val, "16:34")

    def test_clear_alarm_changes_current_alarm_time(self):
        """Does clear_alarm process the correct cleanup tasks:
         * set user information labels
         * set active alarm time to empty string
        """
        self.settings_window.clear_alarm()

        val = self.settings_window.input_alarm_time_label.text()
        self.assertEqual(val, "  :  ")

        val = self.settings_window.alarm_time_status_label.text()
        self.assertEqual(val, "Alarm cleared")

        self.assertEqual(self.settings_window.current_alarm_time, "")

        val = self.settings_window.alarm_time_error_label.text()
        self.assertEqual(val, "")

if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(ClockGUITestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)