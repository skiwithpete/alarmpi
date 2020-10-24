import pytest
import requests
from unittest.mock import patch

from src.handlers import get_open_weather, get_next_trains



@patch("src.handlers.get_next_trains.TrainParser.fetch_daily_train_data")
def test_failed_train_api_request_returns_error_template(mock_fetch_daily_train_data):
    """Does get_next_trains.run return None if API call fails"""
    mock_fetch_daily_train_data.side_effect = requests.exceptions.RequestException()
    parser = get_next_trains.TrainParser()
    res = parser.run()

    assert res is None

@patch("src.handlers.get_open_weather.OpenWeatherMapClient.get_weather")
def test_failed_weather_api_request_returns_error_template(mock_get_weather):
    """Does get_next_trains.run return None if API call fails"""
    mock_get_weather.side_effect = requests.exceptions.RequestException()

    section_data = {"credentials": None, "city_id": None, "units": None}
    parser = get_open_weather.OpenWeatherMapClient(section_data)
    res = parser.fetch_and_format_weather()

    assert res is None
