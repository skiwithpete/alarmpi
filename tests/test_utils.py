#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import datetime
from unittest import TestCase

import utils


class UtilsTestCase(TestCase):
    """Test cases for alarmenv: are properties read from the configuration file
    correctly?
    """

    def test_weekend_with_friday_after_target_time(self):
        """Does weekend return True with a date matching friday after target_time?"""
        offset = 8
        d = datetime.datetime(2019, 1, 18, 13, 27)
        target_time = "7:02"

        res = utils.weekend(d, offset, target_time)
        self.assertTrue(res)

    def test_weekend_with_sunday_after_offset(self):
        """Does weekend with a date outside the offset retrun False?"""
        offset = 10
        d = datetime.datetime(2019, 1, 20, 23, 22)
        target_time = "7:02"

        res = utils.weekend(d, offset, target_time)
        self.assertFalse(res)

    def test_nighttime_with_night_hour(self):
        """Does weekend return True with a date matching friday after target_time?"""
        offset = 8
        d = datetime.datetime(2019, 1, 18, 1, 14)
        target_time = "7:02"

        res = utils.nighttime(d, offset, target_time)
        self.assertTrue(res)

    def test_nighttime_with_day_hour(self):
        """Does weekend return True with a date matching friday after target_time?"""
        offset = 8
        d = datetime.datetime(2019, 1, 18, 14, 14)
        target_time = "7:02"

        res = utils.nighttime(d, offset, target_time)
        self.assertFalse(res)


if __name__ == "__main__":
    """Create test suites from both classes and run tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(UtilsTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
