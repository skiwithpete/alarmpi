#!/usr/bin/python
# -*- coding: utf-8 -*-


import datetime
import unittest
from unittest import TestCase
from unittest.mock import patch
from unittest.mock import MagicMock

import clock


class ClockTestCase(TestCase):
    """Test cases for logic functions for determining alarm time in Clock."""

    @classmethod
    @patch("clock.CronWriter.get_current_alarm")
    def setUpClass(self, mock_get_current_alarm):
        mock_get_current_alarm.return_value = "17:00"  # mock out cron read call
        self.app = clock.Clock("")

    def tearDown(self):
        """Set Clock instance variables back to initial values."""
        self.app.alarm_time_var.set("00:00")

    def test_hour_update_alarm_display_time(self):
        """Does update_alarm_display_time set proper value on hour input?"""
        self.app.update_alarm_display_time("hour", 2)
        new_value = self.app.alarm_time_var.get()
        self.assertEqual(new_value, "02:00")

    def test_minute_update_alarm_display_time(self):
        """Does update_alarm_display_time set proper value on minute input?"""
        self.app.update_alarm_display_time("minute", 10)
        new_value = self.app.alarm_time_var.get()
        self.assertEqual(new_value, "00:10")

    @patch("clock.Clock.is_weekend_after_alarm")
    def test_alarm_indicator_off_during_weekend(self, mock_weekend):
        """Is active alarm indicator in the main window set off during the weekend?"""
        mock_weekend.return_value = True

        self.app.update_active_alarm_indicator(None)
        new_value = self.app.clock_alarm_indicator_var.get()
        self.assertEqual(new_value, "")

    @patch("clock.Clock.is_weekend_after_alarm")
    def test_alarm_indicator_on_during_weekdays(self, mock_weekend):
        """Is active alarm indicator in the main window set pn during weekdays?"""
        mock_weekend.return_value = False

        self.app.update_active_alarm_indicator(None)
        new_value = self.app.clock_alarm_indicator_var.get()
        self.assertEqual(new_value, "17:00")


class CronWriterTestCase(TestCase):
    """Test cases for CronWriter class: do writing and reading from crontab work correctly?"""

    @classmethod
    def setUpClass(self):
        self.cron_writer = clock.CronWriter("")

    @patch("subprocess.check_output")
    def test_empty_string_returned_as_alarm_when_no_alarm_set(self, mock_subprocess_check_output):
        """Does get_current_alarm return an empty string if no alarm in crontab?"""

        # setup a mock crontab with no call to sound_the_alarm.py
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        0 5 * * 1 tar -zcf /var/backups/home.tgz /home/

        """.encode("utf8")  # return value should be bytes
        res = self.cron_writer.get_current_alarm()
        self.assertEqual(res, "")

    @patch("subprocess.check_output")
    def test_alarm_time_returned_when_alarm_set(self, mock_subprocess_check_output):
        """Does get_current_alarm return the corresponding alarm time if alarm is set?"""
        path = self.cron_writer.alarm_path
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
        alarm_line = "16 4 * * 1-5 python {}".format(self.cron_writer.alarm_path)
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        1 2 * *  3 command arg
        {}
        4 5 * * * command2 arg2

        """.format(alarm_line).encode("utf8")
        res = self.cron_writer.get_crontab_lines_without_alarm()

        self.assertNotIn(alarm_line, res)

    def test_invalid_config_file_raises_error(self):
        """Does calling validate_config_path with invalid config file path rase
        RuntimeError?
        """
        self.assertRaises(RuntimeError, self.cron_writer.validate_config_path)


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(CronWriterTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(ClockTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
