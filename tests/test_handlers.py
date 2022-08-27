import requests
from unittest.mock import patch, mock_open

from src.handlers import get_weather, get_next_trains



def test_failing_train_api_request():
    """Test responses sent on failing train API calls"""
    parser = get_next_trains.TrainParser({"station_code": "XYZ"})

    # Error raised during request
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Something went wrong")
        res = parser.run()
        assert res == {"error": {"message": "Something went wrong", "status_code": 503}}

    # Unsuccesful response from the API
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Something went wrong"
        res = parser.run()
        assert res == {"error": {"message": "Something went wrong", "status_code": 500}}

def test_failing_weather_api_request():
    """Test responses sent on failing weather API calls"""
    # Mock opening non existing credentials file
    section_data = {"credentials": None, "city_id": None, "units": None}
    with patch("builtins.open", mock_open(read_data="data")) as mock_file:
        parser = get_weather.OpenWeatherMapClient(section_data)

    # Error raised during request
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        res = parser.fetch_and_format_weather()
        assert res == {"error": {"message": "Network error", "status_code": 503}}

        # Is the TTS content set to a generic error message
        parser.build()
        parser.content = "Failed to read openweathermap.org. "

    # Invalid response
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Something went wrong"
        res = parser.fetch_and_format_weather()
        assert res == {"error": {"message": "Something went wrong", "status_code": 500}}
