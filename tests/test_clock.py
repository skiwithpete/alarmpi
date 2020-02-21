#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest
from unittest import TestCase
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication

from src import clock
from src import GUIWidgets


app = QApplication(sys.argv)


class ClockTestCase(TestCase):
    """Test cases for logic functions for determining alarm time in Clock."""

    @patch("src.alarmenv.AlarmEnv.get_value")
    @patch("src.alarmenv.AlarmEnv.setup")
    @patch("src.clock.CronWriter.get_current_alarm")
    def setUp(self, mock_get_current_alarm, mock_env_setup, mock_get_value):
        mock_get_current_alarm.return_value = "17:00"  # mock out cron read call
        mock_env_setup.side_effect = None  # mock out env setup
        mock_get_value.return_value = "-radio_arg radio_arg_value"
        self.app = clock.Clock("dummy.config")
        self.app.cron = unittest.mock.Mock()  # mock out CronWriter creation
        self.app.env.is_rpi = False

    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    def test_main_window_active_alarm_label_cleared_on_screen_wakeup(self, mock_display):
        """Is the main window label for alarm time cleared on screen wakeup signal handler?"""
        self.app.wakeup_signal_handler(None, None)
        mock_display.assert_called_with("")


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


class CronWriterTestCase(TestCase):
    """Test cases for CronWriter: do writing and reading from crontab work correctly?"""

    @classmethod
    def setUpClass(self):
        self.cron_writer = clock.CronWriter("dummy.config")

    @patch("subprocess.check_output")
    def test_empty_string_returned_as_alarm_when_no_alarm_in_crontab(self, mock_subprocess_check_output):
        """Does get_current_alarm return an empty response if no alarm in crontab?"""

        # setup a mock crontab with no call to alarm_builder.py
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        0 5 * * 1 tar - zcf / var/backups/home.tgz / home/

        """.encode("utf8")  # return value should be bytes
        res = self.cron_writer.get_current_alarm()
        expected_res = (False, "")
        self.assertEqual(res, expected_res)

    @patch("subprocess.check_output")
    def test_alarm_time_returned_when_alarm_in_crontab(self, mock_subprocess_check_output):
        """Does get_current_alarm return the corresponding alarm time if alarm is set?"""
        path = self.cron_writer.path_to_alarm_runner
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow command

        16 4 * * * python {}

        """.format(path).encode("utf8")
        res = self.cron_writer.get_current_alarm()
        expected_res = (True, "04:16")

        self.assertEqual(res, expected_res)

    @patch("subprocess.check_output")
    def test_alarm_status_is_disabled_when_commented_out_in_crontab(self, mock_subprocess_check_output):
        """Does get_current_alarm return the alarm with a disabled status when alarm is commented out?"""
        path = self.cron_writer.path_to_alarm_runner
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow command

        # 16 4 * * * python {}

        """.format(path).encode("utf8")
        res = self.cron_writer.get_current_alarm()
        expected_res = (False, "04:16")

        self.assertEqual(res, expected_res)

    @patch("subprocess.check_output")
    def test_crontab_lines_returned_without_alarm(self, mock_subprocess_check_output):
        """Does get_crontab_lines_without_alarm return all lines except the one containing
        the alarm?
        """
        alarm_line = "16 4 * * * python {}".format(self.cron_writer.path_to_alarm_runner)
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow command

        1 2 * * 3 command1 arg1
        {}
        4 5 * * * command2 arg2

        """.format(alarm_line).encode("utf8")
        res = self.cron_writer.get_crontab_lines_without_alarm()

        self.assertNotIn(alarm_line, res)


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(ClockTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(CronWriterTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(RadioStreamerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
