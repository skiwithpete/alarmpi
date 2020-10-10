import pytest

from PyQt5.QtWidgets import QApplication

from src import GUIWidgets


# Create a gobal QApplication instance to handle windgets
app = QApplication([])


@pytest.fixture
def settings_window():
    return GUIWidgets.SettingsWindow()


def test_hour_update_alarm_display_time(settings_window):
    """Does update_input_alarm_display write the correct time value to the
    settings window's set alarm time label?
    """
    # @pytest.mark.parametrize seems to execute the options
    # in the wrong order.

    # Manually empty the label and add the first digit
    settings_window.input_alarm_time_label.setText(
        GUIWidgets.SettingsWindow.ALARM_LABEL_EMPTY
    )
    settings_window.update_input_alarm_display("0")
    assert settings_window.input_alarm_time_label.text() == "0 :  "

    settings_window.update_input_alarm_display("7")
    assert settings_window.input_alarm_time_label.text() == "07:  "

    settings_window.update_input_alarm_display("1")
    assert settings_window.input_alarm_time_label.text() == "07:1 "

    settings_window.update_input_alarm_display("8")
    assert settings_window.input_alarm_time_label.text() == "07:18"

    # 5th call should start from the beginning
    settings_window.update_input_alarm_display("1")
    assert settings_window.input_alarm_time_label.text() == "1 :  "

def test_validate_alarm_input_rejects_invalid_input(settings_window):
    """Does validate_alarm_input reject invalid input format and set user
    information labels accordingly?
    """
    # set the label to an invalid value and call the method
    settings_window.input_alarm_time_label.setText("25:01")
    settings_window.validate_alarm_input()

    # check labels contain expected error values
    error_value = settings_window.alarm_time_error_label.text()
    alarm_time_value = settings_window.input_alarm_time_label.text()

    assert error_value == "ERROR: Invalid time"
    assert alarm_time_value == "  :  "

def test_validate_alarm_input_returns_valid_input(settings_window):
    """Does validate_alarm_input accept valid input?"""
    # set the label to an invalid value and call the method
    settings_window.input_alarm_time_label.setText("16:34")
    assert settings_window.validate_alarm_input() == "16:34"


def test_clear_alarm_changes_current_alarm_time(settings_window):
    """Does clear_alarm process the correct cleanup tasks:
        * set user information labels
        * set active alarm time to empty string
    """
    settings_window.clear_alarm()
    assert settings_window.input_alarm_time_label.text() == "  :  "
    assert settings_window.alarm_time_status_label.text() == "Alarm cleared"
    assert settings_window.current_alarm_time == ""
    assert settings_window.alarm_time_error_label.text() == ""
    