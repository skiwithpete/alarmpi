import pytest
import os.path
from unittest.mock import patch

from src import alarmenv
from src import alarm_builder
from src.handlers import (
    get_google_translate_tts,
    get_festival_tts,
    get_bbc_news,
    get_gcp_tts,
    get_greeting,
    get_open_weather
)


@pytest.fixture
@patch("src.alarmenv.AlarmEnv.get_config_file_path")
def dummy_alarm(mock_get_config_file_path):
    """Create a dummy alarm from test_alarm.conf"""
    mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")

    # Create AlarmEnv and a Alarm
    env = alarmenv.AlarmEnv("")
    env.setup()     # parse and validate the alarm (no need to mock)
    return alarm_builder.Alarm(env)


def test_first_enabled_tts_client_chosen(dummy_alarm):
    """Does get_tts_client choose the first enabled client?"""
    dummy_alarm.env.config.set("google_gcp_tts", "enabled", "0")
    dummy_alarm.env.config.set("google_translate_tts", "enabled", "1")
    dummy_alarm.env.config.set("festival_tts", "enabled", "0")

    client = dummy_alarm.get_tts_client()
    assert isinstance(client, get_google_translate_tts.GoogleTranslateTTSManager)

def test_default_TTS_client_chosen_when_none_set(dummy_alarm):
    """Is the Festival client chosen in get_tts_client when none is explicitly enaled?"""
    dummy_alarm.env.config.set("google_gcp_tts", "enabled", "0")
    dummy_alarm.env.config.set("google_translate_tts", "enabled", "0")
    dummy_alarm.env.config.set("festival_tts", "enabled", "0")

    client = dummy_alarm.get_tts_client()
    assert isinstance(client, get_festival_tts.FestivalTTSManager)

@patch("src.alarmenv.AlarmEnv.get_value")
def test_correct_content_parser_chosen(mock_get_value, dummy_alarm):
    """Given a content section, is the correct class chosen in get_content_parser_class?"""
    mock_get_value.side_effect = [
        "get_bbc_news.py",
        "get_festival_tts.py",
        "get_gcp_tts.py",
        "get_google_translate_tts.py",
        "get_greeting.py",
        "get_open_weather.py"
    ]

    # import handler modules
    response_classes = [
        get_bbc_news.NewsParser,
        get_festival_tts.FestivalTTSManager,
        get_gcp_tts.GoogleCloudTTS,
        get_google_translate_tts.GoogleTranslateTTSManager,
        get_greeting.Greeting,
        get_open_weather.OpenWeatherMapClient
    ]

    # run get_content_parser_class for each handler name and compare to the corresponding response_class
    for response_class in response_classes:
        created_class = dummy_alarm.get_content_parser_class("dummy_section")
        assert created_class == response_class

@patch("src.alarmenv.AlarmEnv._testnet")
@patch("src.alarm_builder.Alarm.play_beep")
def test_beep_played_when_no_network(mock_play_beep, mock_testnet, dummy_alarm):
    """Is the beep played when no network connection is detected?"""
    mock_testnet.return_value = False

    dummy_alarm.play("")
    mock_play_beep.assert_called()


@patch("src.alarmenv.AlarmEnv.config_has_match")
@patch("src.alarm_builder.Alarm.play_beep")
def test_beep_played_when_no_readaloud(mock_play_beep, mock_config_has_match, dummy_alarm):
    """Is the beep played when readaloud = 0 is set in the configuration?"""
    mock_config_has_match.return_value = False  # mock TTS detection call

    dummy_alarm.play("dummy_content")
    mock_play_beep.assert_called()

