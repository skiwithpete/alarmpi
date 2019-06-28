#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import datetime
import unittest
from unittest import TestCase
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication

import clock
import GUIWidgets

app = QApplication(sys.argv)


class ClockGUITestCase(TestCase):
    """Test cases for logic functions in GUIWidgets"""

    def setUp(self):
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


class ClockTestCase(TestCase):
    """Test cases for logic functions for determining alarm time in Clock."""

    @patch("alarmenv.AlarmEnv.setup")
    @patch("clock.CronWriter.get_current_alarm")
    def setUp(self, mock_get_current_alarm, mock_setup):
        mock_get_current_alarm.return_value = "17:00"  # mock out cron read call
        self.app = clock.Clock("dummy.config")

    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    @patch("utils.weekend")
    @patch("alarmenv.AlarmEnv.get_value")
    def test_alarm_indicator_off_during_weekend(self, mock_get_value, mock_weekend, mock_display):
        """Is the main window's active alarm indicator blank during the weekend?"""
        mock_weekend.return_value = True
        mock_get_value.side_effect = ["0", "8"]  # include_weekends=0, nightmode_offset=8
        self.app.current_alarm_time = True

        self.app.set_active_alarm_indicator()
        mock_display.assert_called_with("")

    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    @patch("utils.weekend")
    @patch("alarmenv.AlarmEnv.get_value")
    def test_alarm_indicator_on_during_weekdays(self, mock_get_value, mock_weekend, mock_display):
        """Is the main window's active alarm indicator on during weekdays?"""
        mock_weekend.return_value = False
        mock_get_value.side_effect = ["0", "8"]  # include_weekends=0, nightmode_offset=8
        self.app.current_alarm_time = "16:08"

        self.app.set_active_alarm_indicator()
        mock_display.assert_called_with("16:08")


class RadioStreamerTestCase(TestCase):
    """Test cases for RadioStreamer: does streaming radio work correctly?"""

    def setUp(self):
        self.radio = clock.RadioStreamer()

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

    @patch("clock.subprocess.Popen")
    def test_stop_clears_active_process(self, mock_Popen):
        """Does stop clear the list of running processes?"""
        self.radio.play("mock_url")
        self.radio.stop()

        self.assertEqual(self.radio.process, None)


class CronWriterTestCase(TestCase):
    """Test cases for CronWriter: do writing and reading from crontab work correctly?"""

    @classmethod
    def setUpClass(self):
        self.cron_writer = clock.CronWriter("dummy.config")

    @patch("subprocess.check_output")
    def test_empty_string_returned_as_alarm_when_no_alarm_in_crontab(self, mock_subprocess_check_output):
        """Does get_current_alarm return an empty string if no alarm in crontab?"""

        # setup a mock crontab with no call to alarm_builder.py
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        0 5 * * 1 tar - zcf / var/backups/home.tgz / home/

        """.encode("utf8")  # return value should be bytes
        res = self.cron_writer.get_current_alarm()
        self.assertEqual(res, "")

    @patch("subprocess.check_output")
    def test_alarm_time_returned_when_alarm_in_crontab(self, mock_subprocess_check_output):
        """Does get_current_alarm return the corresponding alarm time if alarm is set?"""
        path = self.cron_writer.path_to_alarm
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        16 4 * * 1-5 python {}

        """.format(path).encode("utf8")
        res = self.cron_writer.get_current_alarm()
        self.assertEqual(res, "04:16")

    @patch("subprocess.check_output")
    def test_crontab_lines_returned_without_alarm(self, mock_subprocess_check_output):
        """Does get_crontab_lines_without_alarm return all lines except the one containing
        the alarm?
        """
        alarm_line = "16 4 * * 1-5 python {}".format(self.cron_writer.path_to_alarm)
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        1 2 * *  3 command arg
        {}
        4 5 * * * command2 arg2

        """.format(alarm_line).encode("utf8")
        res = self.cron_writer.get_crontab_lines_without_alarm()

        self.assertNotIn(alarm_line, res)


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(ClockTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(ClockGUITestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(CronWriterTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(RadioStreamerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
