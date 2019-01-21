#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import unittest
from unittest import TestCase
from unittest.mock import patch

import clock


class ClockTestCase(TestCase):
    """Test cases for logic functions for determining alarm time in Clock."""

    @patch("clock.RadioStreamer")
    @patch("alarmenv.AlarmEnv.setup")
    @patch("clock.CronWriter.get_current_alarm")
    def setUp(self, mock_get_current_alarm, mock_setup, mock_RadioStreamer):
        mock_get_current_alarm.return_value = "17:00"  # mock out cron read call
        self.app = clock.Clock("")

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

    @patch("clock.Clock.set_alarm_status_message")
    @patch("clock.CronWriter.add_cron_entry")
    def test_set_alarm_changes_current_alarm_time(self, mock_add_cron_entry, mock_set_status_message):
        """Does set_alarm process the correct tasks:
          1 call CronWriter
          2 update the internal alarm time instance variable
          3 write status message to alarm setup window for user
        """
        # run update_alarm_display_time so set_alarm reads a value other than 00:00
        self.app.update_alarm_display_time("hour", 17)
        self.app.set_alarm()

        # was CronWriter used?
        mock_add_cron_entry.assert_called()

        # was current_alarm_time changed?
        res = self.app.current_alarm_time
        self.assertEqual(res, "17:00")

        # was a new status message written to the setup window?
        mock_set_status_message.assert_called()

    @patch("clock.CronWriter.delete_cron_entry")
    def test_clear_alarm_changes_current_alarm_time(self, mock_delete_cron_entry):
        """Does clear_alarm process proper clearing tasks?"""
        # run update_alarm_display_time so set_alarm reads a value other than 00:00
        self.app.create_alarm_window()
        self.app.clear_alarm()

        # was CronWriter used?
        mock_delete_cron_entry.assert_called()

        # was current_alarm_time changed?
        res = self.app.current_alarm_time
        self.assertEqual(res, "")

    @patch("clock.utils.weekend")
    def test_alarm_indicator_off_during_weekend(self, mock_weekend):
        """Is the main window's active alarm indicator blank during the weekend?"""
        mock_weekend.return_value = True

        self.app.set_active_alarm_indicator()
        new_value = self.app.clock_alarm_indicator_var.get()
        self.assertEqual(new_value, "")

    @patch("clock.utils.weekend")
    def test_alarm_indicator_on_during_weekdays(self, mock_weekend):
        """Is the main window's active alarm indicator on during weekdays?"""
        mock_weekend.return_value = False

        self.app.set_active_alarm_indicator()
        new_value = self.app.clock_alarm_indicator_var.get()
        self.assertEqual(new_value, "17:00")

    def test_play_radio_opens_stream_when_not_opened(self):
        """Does play_radio open a new radio stream if one is not already playing?"""
        self.app.radio.is_playing.return_value = False

        # Create necessary instance attributes to ensure this test will run
        # as these aren't created in __init__,
        # An ugly hack :(
        self.app.radio_button = clock.tk.Button()
        self.app.env.radio_url = "mock_url"

        self.app.play_radio()
        self.app.radio.play.assert_called_with("mock_url")

    def test_play_radio_closes_existing_stream(self):
        """Does play_radio close existing stream when one is already playing?"""
        self.app.radio.is_playing.return_value = True

        self.app.radio_button = clock.tk.Button()
        self.app.play_radio()
        self.app.radio.stop.assert_called()


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
        self.cron_writer = clock.CronWriter()

    @patch("subprocess.check_output")
    def test_empty_string_returned_as_alarm_when_no_alarm_set(self, mock_subprocess_check_output):
        """Does get_current_alarm return an empty string if no alarm in crontab?"""

        # setup a mock crontab with no call to sound_the_alarm.py
        mock_subprocess_check_output.return_value = """
        # Mock crontable
        # m h  dom mon dow   command

        0 5 * * 1 tar - zcf / var/backups/home.tgz / home/

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

    suite = unittest.TestLoader().loadTestsFromTestCase(ClockTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(RadioStreamerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
