import pytest
import os.path
import configparser

from unittest.mock import patch

from src import alarmenv



@pytest.fixture
@patch("src.alarmenv.AlarmEnv.get_config_file_path")
def dummy_env(mock_get_config_file_path):
    mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")

    # Create an AlarmEnv from the configuration above with empty string as dummy name
    env = alarmenv.AlarmEnv("")
    env.setup()
    return env


@patch("src.alarmenv.AlarmEnv.get_sections")
def test_validate_config_raises_runtime_error_on_invalid_options(mock_get_sections, dummy_env):
    """Does validate_config raise RuntimeError when configparser detects invalid
    options?
    """
    mock_get_sections.side_effect = configparser.NoSectionError("")
    with pytest.raises(RuntimeError):
        dummy_env.validate_config()

@patch("src.alarmenv.AlarmEnv.get_config_file_path")
def test_invalid_config_file_raises_error(mock_get_config_file_path):
    """Does trying to create an AlarmEnv with a non-existing configuration file
    raise RuntimeError?
    """
    # Create a new AlarmEnv without calling setup on it.
    mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.conf")
    env = alarmenv.AlarmEnv("")

    # Set the file path to non-existing file
    env.config_file = "dummy.conf"
    with pytest.raises(RuntimeError):
        env.setup()

def test_no_match_on_invalid_config_section(dummy_env):
    """Does config_has_match return False (instead of an Exception) when checking for invalid section?"""
    assert not dummy_env.config_has_match("invalidsection", "enabled", "1")

def test_match_on_valid_config_keys(dummy_env):
    """Does config_has_match return True on valid section, option, key combination?"""
    assert dummy_env.config_has_match("BBC_news", "enabled", "1")

def test_get_sections_with_exclusions(dummy_env):
    """Does get_sections return correct section names when called with exclusions?"""
    read_sections = dummy_env.get_sections(excludes=["main", "greeting"])
    filtered_sections = [
        "alarm",
        "plugins",
        "openweathermap",
        "BBC_news",
        "google_gcp_tts",
        "google_translate_tts",
        "festival_tts",
        "radio"
    ]

    assert set(read_sections) == set(filtered_sections)

def test_read_content_sections(dummy_env):
    """Does get_enabled_sections return correct 'content' section names?"""
    assert dummy_env.get_enabled_sections("content") == ["BBC_news"]

