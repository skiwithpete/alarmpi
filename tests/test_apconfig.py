import pytest
import os.path

from unittest.mock import patch

from src import apconfig



@pytest.fixture
@patch("src.apconfig.AlarmConfig.get_config_file_path")
def dummy_env(mock_get_config_file_path):
    # Create an AlarmEnv from the configuration above with empty string as dummy name
    mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.yaml")
    return apconfig.AlarmConfig("")

def test_invalid_config_file_raises_error():
    """Does trying to create an AlarmConfig with a non-existing configuration file
    raise FileNotFoundError?
    """
    with pytest.raises(FileNotFoundError):
        config = apconfig.AlarmConfig("no_such_file.conf")

def test_validate_on_invalid_brightness(dummy_env):
    """Does validate_config raise AssertionError on invalid brightness?"""
    dummy_env.config["main"]["low_brightness"] = 300
    with pytest.raises(AssertionError):
        dummy_env.validate()

def test_validate_on_too_many_tts(dummy_env):
    """Does validate_config raise AssertionError on multiple enabled TTS engines?"""
    dummy_env.config["TTS"]["GCP"]["enabled"] = True
    dummy_env.config["TTS"]["festival"]["enabled"] = True
    with pytest.raises(AssertionError):
        dummy_env.validate()

def test_read_content_sections(dummy_env):
    """Does get_enabled_sections return enabled 'content' section names?"""
    assert set(dummy_env.get_enabled_sections("content").keys()) == {"BBC_news", "openweathermap.org"}
