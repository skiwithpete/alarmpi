import pytest
import os.path
import requests
from unittest.mock import patch, Mock

from freezegun import freeze_time

from src import apconfig
from src import alarm_builder
from src.handlers import (
    get_google_translate_tts,
    get_festival_tts,
    get_bbc_news,
    get_gcp_tts,
    get_greeting,
    get_weather
)


@pytest.fixture
@patch("src.apconfig.AlarmConfig.get_config_file_path")
def dummy_alarm_builder(mock_get_config_file_path):
    """Create a dummy alarm from test_alarm.conf"""
    mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.yaml")

    config = apconfig.AlarmConfig("")
    config["main"]["alarm_time"] = None
    return alarm_builder.AlarmBuilder(config)

def test_enabled_tts_client_chosen(dummy_alarm_builder):
    """Does get_tts_client choose the enabled client?"""
    dummy_alarm_builder.config["TTS"]["GCP"]["enabled"] = False
    dummy_alarm_builder.config["TTS"]["google_translate"]["enabled"] = True
    dummy_alarm_builder.config["TTS"]["festival"]["enabled"] = False

    client = dummy_alarm_builder.get_tts_client()
    assert isinstance(client, get_google_translate_tts.GoogleTranslateTTSManager)

def test_default_TTS_client_chosen_when_none_set(dummy_alarm_builder):
    """Is the Festival client chosen in get_tts_client when none is explicitly enaled?"""
    dummy_alarm_builder.config["TTS"]["GCP"]["enabled"] = False
    dummy_alarm_builder.config["TTS"]["google_translate"]["enabled"] = False
    dummy_alarm_builder.config["TTS"]["festival"]["enabled"] = False

    client = dummy_alarm_builder.get_tts_client()
    assert isinstance(client, get_festival_tts.FestivalTTSManager)

def test_correct_content_parser_chosen(dummy_alarm_builder):
    """Given a content section, is the correct class chosen in get_content_parser_class?"""
    handler_map = {
        "get_bbc_news.py": get_bbc_news.NewsParser,
        "get_festival_tts.py": get_festival_tts.FestivalTTSManager,
        "get_gcp_tts.py": get_gcp_tts.GoogleCloudTTS,
        "get_google_translate_tts.py": get_google_translate_tts.GoogleTranslateTTSManager,
        "get_greeting.py":  get_greeting.Greeting,
        "get_weather.py": get_weather.OpenWeatherMapClient
    }

    for module, class_ in handler_map.items():
        created_class = dummy_alarm_builder.get_content_parser_class({"handler": module})
        assert created_class == class_

@patch("src.alarm_builder.AlarmBuilder.play_beep")
def test_beep_played_when_tts_fails(mock_play_beep, dummy_alarm_builder):
    """Is the beep played when no network connection is detected?"""
    dummy_alarm_builder.tts_client = Mock()
    dummy_alarm_builder.tts_client.play.side_effect = requests.exceptions.HTTPError

    dummy_alarm_builder.play("dummy content")
    mock_play_beep.assert_called()

@patch("src.alarm_builder.AlarmBuilder.play_beep")
def test_beep_played_when_tts_disabled(mock_play_beep, dummy_alarm_builder):
    """Is the beep played when TTS is disabled in the configuration?"""
    dummy_alarm_builder.config["main"]["TTS"] = False

    dummy_alarm_builder.play("dummy content")
    mock_play_beep.assert_called()

def test_alarm_time_override(dummy_alarm_builder):
    """Is alarm time overridden when value specified in config?"""
    dummy_alarm_builder.config["main"]["alarm_time"] = "20:21"
    greeting = dummy_alarm_builder.generate_greeting()
    assert "The time is 08:21" in greeting

@freeze_time("2021-07-30 11:10")
def test_alarm_time_without_override(dummy_alarm_builder):
    """Is alarm time current time?"""
    greeting = dummy_alarm_builder.generate_greeting()
    assert "The time is 11:10" in greeting