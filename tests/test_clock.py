#!/usr/bin/python
# -*- coding: utf-8 -*-


import unittest
from unittest import TestCase
from unittest.mock import patch

import clock


class CronWriterTestCase(TestCase):
    """Test cases for CronWriter class: do writing and reading from crontab work correctly?"""

    @classmethod
    def setUpClass(self):
        self.cron_writer = clock.CronWriter()

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


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(CronWriterTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
