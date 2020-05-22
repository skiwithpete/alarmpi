#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import datetime
from unittest import TestCase

from src import utils


class UtilsTestCase(TestCase):
    """Test cases for alarmenv: are properties read from the configuration file
    correctly?
    """
    def test_nighttime_with_night_hour(self):
        """Does nightime return True when called with compare_times matching
        the targeted nighttime offset?
        """
        offset = 8

        compare_time = "01:14"
        target_time = "07:02"
        res = utils.nighttime(target_time, offset, compare_time)
        self.assertTrue(res)

        compare_time = "12:54"
        target_time = "19:20"
        res = utils.nighttime(target_time, offset, compare_time)
        self.assertTrue(res)

    def test_nighttime_with_day_hour(self):
        """Does nightime return False when called with compare_times outside of
        target_time thresholds?
        """
        offset = 8

        compare_time = "22:14"
        target_time = "07:02"
        res = utils.nighttime(target_time, offset, compare_time)
        self.assertFalse(res)

        compare_time = "07:05"
        target_time = "07:00"
        res = utils.nighttime(target_time, offset, compare_time)
        self.assertFalse(res)


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(UtilsTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
