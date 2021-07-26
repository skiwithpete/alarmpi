import pytest
import os.path
import subprocess
from unittest.mock import patch, Mock
from PyQt5.QtWidgets import QApplication

from src import clock


# Create a gobal QApplication instance to handle windgets
app = QApplication([])


@pytest.fixture(scope="class")
@patch("src.apconfig.AlarmConfig.get_config_file_path")
def dummy_clock(mock_get_config_file_path):
    mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.yaml")

    # Create a Clock instance from the configuration above with empty string as dummy name
    dummy_clock = clock.Clock("")
    dummy_clock.setup()
    return dummy_clock


class TestClockCase():
    """Test cases for logic functions for determining alarm time in Clock."""

    @patch("src.GUIWidgets.SettingsWindow.validate_alarm_input")
    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    def test_set_alarm_updates_screen_and_sets_timers(self, mock_display, mock_validate_alarm_input, dummy_clock):
        """Does 'Set alarm' button start timers for alarm build and play and update
        main window and settings window labels?
        """
        mock_validate_alarm_input.return_value = "00:10"  # Mock validating a not-set alarm time
        dummy_clock.settings_window.numpad_buttons["set"].click()

        assert dummy_clock.alarm_timer.isActive()
        assert dummy_clock.alarm_build_timer.isActive()

        mock_display.assert_called_with("00:10")

        settings_window_value = dummy_clock.settings_window.alarm_time_status_label.text()
        assert settings_window_value == "Alarm set for 00:10"

        # Also check get_current_active_alarm returns a value
        active_alarm = dummy_clock.get_current_active_alarm()
        assert active_alarm is not None

    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    def test_clear_alarm_clears_screen_and_stops_timers(self, mock_display, dummy_clock):
        """Does 'Clearm alarm' button stop timers for alarm build and play and clear
        main window and settings window labels?
        """
        dummy_clock.settings_window.numpad_buttons["clear"].click()
        assert not dummy_clock.alarm_timer.isActive()
        assert not dummy_clock.alarm_build_timer.isActive()

        mock_display.assert_called_with("")

        settings_window_value = dummy_clock.settings_window.alarm_time_status_label.text()
        assert settings_window_value == "Alarm cleared"

    @patch("PyQt5.QtWidgets.QLCDNumber.display")
    @patch("src.rpi_utils.set_display_backlight_brightness")
    def test_play_alarm_starts_alarm_play_thread(self, mock_set_display_backlight_brightness, mock_display, dummy_clock):
        """Does the timer slot function for playing the alarm set window brightness,
        clearn main window label and start the alarm play thread?
        """
        dummy_clock.alarm_play_thread.start = Mock()
        dummy_clock.enable_screen_and_show_control_buttons = Mock()

        dummy_clock.play_alarm()
        mock_display.assert_called_with("")
        mock_set_display_backlight_brightness.assert_called_with(255)
        dummy_clock.alarm_play_thread.start.assert_called()

    @patch("src.clock.Clock.play_radio")
    def test_finish_playing_alarm_starts_radio_if_enabled(self, mock_play_radio, dummy_clock):
        """Does the alarm finish callback call the radio thread when radio is enabled?"""
        dummy_clock.config["radio"]["enabled"] = True
        dummy_clock.main_window.control_buttons["Radio"] = Mock()

        dummy_clock.finish_playing_alarm()
        mock_play_radio.assert_called_with(url="www.example.com")

    def test_settings_window_keeps_previously_set_alarm(self, dummy_clock):
        """Does the settings window input label for set alarm time keep
        its value when the settings window is closed?
        """
        # Mock the actual window display calls
        dummy_clock.settings_window.show = Mock()
        dummy_clock.settings_window.close = Mock()
        dummy_clock.play_radio = Mock()

        dummy_clock.settings_window.set_alarm_input_time_label("07:16")
        dummy_clock.settings_button.click()

        # Test value when settings window is open
        label_time = dummy_clock.settings_window.input_alarm_time_label.text()
        assert label_time == "07:16"

        # Close the window and test the value again
        dummy_clock.settings_window.clear_labels_and_close()
        label_time = dummy_clock.settings_window.input_alarm_time_label.text()
        assert label_time == "07:16"

        # Simulate alarm play finish and test the value again
        dummy_clock.main_window.control_buttons["Radio"] = Mock()
        dummy_clock.finish_playing_alarm()
        label_time = dummy_clock.settings_window.input_alarm_time_label.text()
        assert label_time == "07:16"

    @patch("src.rpi_utils.set_display_backlight_brightness")
    @patch("src.rpi_utils.get_current_display_backlight_brightness")
    def test_brightness_toggle(self, mock_get_brightness, mock_set_brightness, dummy_clock):
        """Does the backlight toggle change brightness change from low to high?"""
        mock_get_brightness.return_value = 12

        # Ensure the button is enabled before clicking it
        dummy_clock.settings_window.control_buttons[2].setEnabled(True)
        dummy_clock.settings_window.control_buttons[2].click()
        mock_set_brightness.assert_called_with(255)

        # Click again and check value is set back to low
        mock_get_brightness.return_value = 255
        dummy_clock.settings_window.control_buttons[2].click()
        mock_set_brightness.assert_called_with(12)  # Default low brightness value is 12

    @patch("src.apconfig.AlarmConfig.get_config_file_path")
    def test_brightness_buttons_disabled_on_non_writable_configs(self, mock_get_config_file_path):
        """Are the brightness buttons disabled when the undelying system configurations files
        are not writable?
        """
        # Since we want to intercept the AlarmConfig property rpi_brightness_write_access, create a
        # distinct Clock object separate from the fixture and force the value to False
        # before the button status is checked in setup()
        mock_get_config_file_path.return_value = os.path.join(os.path.dirname(__file__), "test_alarm.yaml")
        dummy_clock = clock.Clock("")
        dummy_clock.config.rpi_brightness_write_access = False
        dummy_clock.setup()
        
        assert not dummy_clock.settings_window.control_buttons[2].isEnabled()
        assert not dummy_clock.main_window.control_buttons["Blank"].isEnabled()


@pytest.fixture
def dummy_radio():
    radio_args = {"args": "-playlist url", "url": ""}
    return clock.RadioStreamer(radio_args)

class TestRadioStreamerCase():
    """Test cases for RadioStreamer: does streaming radio work correctly?"""

    def test_radio_not_playing_on_empty_process(self, dummy_radio):
        """Does is_playing return False when the active process flag is not set?"""
        dummy_radio.process = None
        assert not dummy_radio.is_playing()

    def test_radio_is_playing_on_non_empty_process(self, dummy_radio):
        """Does is_playing return True when an active process flag is set?"""
        dummy_radio.process = True
        assert dummy_radio.is_playing()

    def test_stop_clears_active_process(self, dummy_radio):
        """Does stop clear the list of running processes?"""
        subprocess.Popen = Mock()
        dummy_radio.play("https://foo.bar")
        dummy_radio.stop()

        assert dummy_radio.process is None
