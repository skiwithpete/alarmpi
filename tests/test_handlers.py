import requests
from unittest.mock import patch, mock_open

from src.handlers import get_weather, get_next_trains



@patch("src.handlers.get_next_trains.TrainParser.fetch_daily_train_data")
def test_failed_train_api_request_returns_error_template(mock_fetch_daily_train_data):
    """Does get_next_trains.run return None if API call fails"""
    mock_fetch_daily_train_data.side_effect = requests.exceptions.RequestException()
    parser = get_next_trains.TrainParser(None)
    res = parser.run()

    assert res is None

@patch("src.handlers.get_weather.OpenWeatherMapClient.get_weather")
def test_failed_weather_api_request_returns_error_template(mock_get_weather):
    """Does fetch_and_format_weather return None if API call fails"""
    mock_get_weather.side_effect = requests.exceptions.RequestException()

    section_data = {"credentials": None, "city_id": None, "units": None}

    # Mock opening non existing credentials file
    with patch("builtins.open", mock_open(read_data="data")) as mock_file:
        parser = get_weather.OpenWeatherMapClient(section_data)
        res = parser.fetch_and_format_weather()

        assert res is None
