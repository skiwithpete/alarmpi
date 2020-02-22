#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import datetime
import requests
from unittest import TestCase
from unittest.mock import patch

from src.handlers import get_open_weather, get_next_trains


class HandlerTestCase(TestCase):
    """Test cases for the various handler."""

    @patch("src.handlers.get_next_trains.TrainParser.fetch_daily_train_data")
    def test_failed_train_api_request_returns_error_template(self, mock_fetch_daily_train_data):
        """Does get_next_trains.run return a dict of ERRs if API call fails"""
        mock_fetch_daily_train_data.side_effect = requests.exceptions.RequestException()
        parser = get_next_trains.TrainParser()
        res = parser.run()

        KEYS = [
            "liveEstimateTime",
            "scheduledTime",
            "commuterLineID",
            "cancelled",
            "sortKey"
        ]
        error_response = {key: "ERR" for key in KEYS}
        self.assertEqual(res, [error_response] * 3) 

    @patch("src.handlers.get_open_weather.OpenWeatherMapClient.get_weather")
    def test_failed_weather_api_request_returns_error_template(self, mock_get_weather):
        """Does get_next_trains.run return a dict of ERRs if API call fails"""
        mock_get_weather.side_effect = requests.exceptions.RequestException()

        section_data = {"key_file": None, "city_id": None, "units": None}
        parser = get_open_weather.OpenWeatherMapClient(section_data)
        res = parser.fetch_and_format_weather()

        error_response = {key: "ERR" for key in parser.RETURN_TEMPLATE_KEYS}
        self.assertEqual(res, error_response)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(HandlerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
