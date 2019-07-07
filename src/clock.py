#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""A PyQt5 clock radio application."""


import time
import datetime
import os
import sys
import subprocess
import signal
import logging
import json

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap

from src import alarmenv
from src import utils
from src import alarm_builder
from src import GUIWidgets
from src import rpi_utils
from src.handlers import get_open_weather, get_next_trains


class Clock:
    """Wrapper class for the clock itself. Defines interactions between
    UI elements and backend logic.
    """

    def __init__(self, config_file, **kwargs):
        """Setup GUI windows and various configuration objects.
        params
            config_file (str): name (not path!) of the configuration file in /configs to use.
            kwargs (dict): additional command line paramters passed from main.py
        """
        self.main_window = GUIWidgets.AlarmWindow()
        self.settings_window = GUIWidgets.SettingsWindow()

        # Read the alarm configuration file and initialize and alarmenv object
        self.config_file = config_file
        self.env = alarmenv.AlarmEnv(config_file)
        self.env.setup()

        self.cron = CronWriter(config_file)
        self.radio = RadioStreamer()
        self.alarm_player = alarm_builder.Alarm(self.env)
        self.train_parser = get_next_trains.TrainParser()

        if self.env.get_value("openweathermap", "enabled", fallback="0") == "1":
            section = self.env.get_section("openweathermap")
            self.weather_parser = get_open_weather.OpenWeatherMapClient(section)

        if kwargs.get("fullscreen"):
            self.main_window.showFullScreen()
            self.main_window.setCursor(Qt.BlankCursor)
            self.settings_window.setCursor(Qt.BlankCursor)

        if kwargs.get("debug"):
            self.env.config.set("polling", "weather", "0")
            self.env.config.set("polling", "train", "0")
            self.main_window.keyPressEvent = self.debug_key_press_event

    def setup(self):
        """Setup various button handlers as well as weather and train data polling
        for the main windows side bar.
        """
        self.setup_button_handlers()

        weather_enabled = self.env.get_value("openweathermap", "enabled") == "1"
        weather_api_key_exists = self.env.get_value("openweathermap", "key_file", fallback=False)
        weather_polling_enabled = self.env.get_value("polling", "weather", fallback=False) == "1"

        train_polling_enabled = self.env.get_value("polling", "train", fallback=False) == "1"

        if weather_enabled and weather_api_key_exists and weather_polling_enabled:
            self.setup_weather_polling()

        if train_polling_enabled:
            self.setup_train_polling()

        # Setup settings window's checkboxes:
        # set initial values to config values and set handlers
        tts_enabled = self.env.config_has_match("main", "readaloud", "1")
        self.settings_window.readaloud_checkbox.setChecked(tts_enabled)

        # set nightmode as enabled if non zero offset specified in the config
        self.original_nightmode_offset = self.env.get_value(
            "alarm", "nightmode_offset", fallback="8")

        nightmode = (self.original_nightmode_offset != "0")
        self.settings_window.nightmode_checkbox.setChecked(nightmode)

        signal.signal(signal.SIGUSR1, self.radio_signal_handler)
        signal.signal(signal.SIGUSR2, self.wakeup_signal_handler)

        # Set main window's alarm time display to cron's time
        active, self.current_alarm_time = self.cron.get_current_alarm()
        if active:
            self.main_window.alarm_time_lcd.display(self.current_alarm_time)

            # Also set the setting's window notifications: alarm time label
            msg = "current alarm time: {}".format(self.current_alarm_time)
            self.settings_window.alarm_time_status_label.setText(msg)

            # ...and status message on the left panel
            alarm_time_msg = GUIWidgets.SettingsWindow.ALARM_INPUT_SUCCESS.format(
                self.current_alarm_time)
            self.settings_window.alarm_time_status_label.setText(alarm_time_msg)

        # If there's an alarm in cron, set time as the selected time in settings window regardless
        # of whether enabled or not.
        if self.current_alarm_time:
            self.settings_window.input_alarm_time_label.setText(self.current_alarm_time)

        self.screen_blank_timer = QTimer(self.main_window)
        self.screen_blank_timer.setSingleShot(True)
        self.screen_blank_timer.timeout.connect(self.blank_screen_and_hide_control_buttons)

        self.main_window.mouseReleaseEvent = self.on_release_event_handler

    def setup_button_handlers(self):
        """Setup button handlers for the main window and settings window."""
        # Setup references to main control buttons in both windows
        self.settings_button = self.main_window.control_buttons["Settings"]
        self.radio_button = self.main_window.control_buttons["Radio"]
        self.blank_button = self.main_window.control_buttons["Blank"]
        self.close_button = self.main_window.control_buttons["Close"]

        brightness_button = self.settings_window.control_buttons["Toggle brightness"]
        self.alarm_play_button = self.settings_window.control_buttons["Play now"]
        window_button = self.settings_window.control_buttons["Toggle window"]
        alarm_set_button = self.settings_window.numpad_buttons["set"]
        alarm_clear_button = self.settings_window.numpad_buttons["clear"]

        # Disable blank and brightness buttons if host system is not a Raspberry Pi
        if not self.env.is_rpi:
            self.blank_button.setEnabled(False)
            brightness_button.setEnabled(False)

        # Set button handlers for buttons requiring interactions between helper classes
        # ** main window buttons **
        self.settings_button.clicked.connect(self.open_settings_window)

        # Disable the radio button if no url provided in the configuration
        radio_stream_url = self.env.get_value("radio", "url", fallback=False)
        if not radio_stream_url:
            self.radio_button.setEnabled(False)

        # ...otherwise set the button as an on/off toggle
        else:
            self.radio_button.setCheckable(True)
            self.radio_button.clicked.connect(self.play_radio)

        self.blank_button.clicked.connect(self.blank_screen_and_hide_control_buttons)
        self.close_button.clicked.connect(self.cleanup_and_exit)

        # ** settings window buttons **
        brightness_button.clicked.connect(rpi_utils.toggle_display_backlight_brightness)
        self.alarm_play_thread = AlarmPlayThread(self.env)
        self.alarm_play_thread.signal.connect(self.finish_playing_alarm)
        self.alarm_play_button.clicked.connect(self.play_alarm)

        window_button.clicked.connect(self.toggle_display_mode)
        alarm_set_button.clicked.connect(self.set_alarm)
        alarm_clear_button.clicked.connect(self.clear_alarm)

        # Settings window checkboxes
        self.settings_window.readaloud_checkbox.stateChanged.connect(self.enable_tts)
        self.settings_window.nightmode_checkbox.stateChanged.connect(self.enable_nightmode)

    def open_settings_window(self):
        """Callback for opening the settings window. Also clears timer for blanking
        the screen (if active).
        """
        self.screen_blank_timer.stop()
        self.settings_window.show()

    def radio_signal_handler(self, sig, frame):
        """Signal handler for incoming radio stream requests from alarm_builder.
        Opens the stream and sets radio button state as pressed.
        Also clears the main window's alarm display LCD widget if there is no alarm
        the next day.
        """
        self.main_window.control_buttons["Radio"].click()  # emit a click signal

    def wakeup_signal_handler(self, sig, frame):
        """Signal handler for waking up the screen: enable the screen and
        comment out the cron entry.
        """
        if self.env.is_rpi:
            self.enable_screen_and_show_control_buttons()
        self.main_window.alarm_time_lcd.display("")

        self.cron.disable_entry()

    def on_release_event_handler(self, event):
        """Event handler for touching the screen: update the main window's alarm
        time label and, if on a Raspberry Pi and nighttime, set a timeout for blanking
        the screen.
        """
        # If not running on Raspberry Pi exit early
        if not self.env.is_rpi:
            return

        # get screen state before the event occured and set it as enabled
        old_screen_state = rpi_utils.get_and_set_screen_state("on")
        self.show_control_buttons()

        # set screen blanking timeout if the screen was blank before the event
        if old_screen_state == "off":
            self.set_screen_blank_timeout()

    def set_alarm(self):
        """Handler for settings window's 'set' button. Validates the user selected
        time and adds a cron entry (if valid). No alarm is set if value is invalid.
        """
        # overwrite existing line

        time_str = self.settings_window.validate_alarm_input()
        if time_str:
            entry = self.cron.create_entry(time_str)
            self.cron.add_entry(entry)

            alarm_time_msg = GUIWidgets.SettingsWindow.ALARM_INPUT_SUCCESS.format(time_str)
            self.settings_window.alarm_time_status_label.setText(alarm_time_msg)

            # clear the label showing the selected time
            self.settings_window.input_alarm_time_label.setText(
                GUIWidgets.SettingsWindow.ALARM_LABEL_EMPTY)

            # update main window alarm display
            self.main_window.alarm_time_lcd.display(time_str)

    def clear_alarm(self):
        """Handler for settings window's 'clear' button. Removes the cron entry
        (if any) and clears both window's alarm displays.
        """
        self.cron.delete_entry()
        self.settings_window.clear_alarm()
        self.main_window.alarm_time_lcd.display("")

    def set_screen_blank_timeout(self):
        """Blank the screen after a short timeout if it is currently night time
        (ie. nightmode_offset hours before alarm time).
        """
        alarm_time = self.current_alarm_time  # HH:MM
        if not alarm_time:
            return

        offset = int(self.env.get_value("alarm", "nightmode_offset", fallback="0"))
        now = datetime.datetime.now()
        nighttime = utils.nighttime(now, offset, alarm_time)

        # set a new timeout for blanking the screen was blank before the click event
        if nighttime:
            self.screen_blank_timer.start(3*1000)  # 3 second timeout until screen blank

    def play_radio(self):
        """Callback to the 'Play radio' button: open or close the radio stream
        depending on the button state.
        """
        button = self.main_window.control_buttons["Radio"]

        # The radio button is a checkable: it will stay down until pressed again.
        # Therefore the radio should start playing when the button is pressed and
        # stop when not pressed. (The state change happends before this callback runs.)
        button_checked = button.isChecked()
        if button_checked:
            self.radio.play(self.env.radio_url)
        else:
            self.radio.stop()

    def play_alarm(self):
        """Callback to the 'Play now' button: starts playing the alarm in a separate
        thread.
        """
        self.alarm_play_thread.start()
        # Disable the button. As is, clicking the button while the alarm is already playing
        # won't do anything anyway, since the thread playing the alarm is busy.
        self.alarm_play_button.setEnabled(False)

    def finish_playing_alarm(self):
        """Finishing action to playing the alarm: re-enable the button."""
        self.alarm_play_button.setEnabled(True)

    def setup_weather_polling(self):
        """Setup polling for updating the weather every 30 minutes."""
        self.update_weather()
        _timer = QTimer(self.main_window)
        _timer.timeout.connect(self.update_weather)
        _timer.start(30*60*1000)  # 30 minute interval

    def update_weather(self):
        """Update the weather labels on the main window. Makes an API request
        openweathermap.org for current temperature and windspeed.
        """
        logging.info("Updating weather")
        api_response = self.weather_parser.get_weather()
        weather = get_open_weather.OpenWeatherMapClient.format_response(api_response)

        temperature = weather["temp"]
        wind = weather["wind_speed_ms"]

        msg = "{}°C".format(round(temperature))
        self.main_window.temperature_label.setText(msg)

        msg = "{}m/s".format(round(wind))
        self.main_window.wind_speed_label.setText(msg)

        # Update the icon
        icon_id = api_response["weather"][0]["icon"]
        icon_binary = get_open_weather.OpenWeatherMapClient.get_weather_icon(icon_id)

        pixmap = QPixmap()
        pixmap.loadFromData(icon_binary)
        self.main_window.weather_container.setPixmap(pixmap)

    def setup_train_polling(self):
        """Setup polling for next train departure times every 12 minutes."""
        self.update_trains()
        _timer = QTimer(self.main_window)
        _timer.timeout.connect(self.update_trains)
        _timer.start(12*60*1000)

    def update_trains(self):
        """Fetch new train data from DigiTraffic API and display on the right sidebar."""
        logging.info("Updating trains")
        trains = self.train_parser.get_next_3_departures()

        for train, label in zip(trains, self.main_window.train_labels):
            line_id = train["commuterLineID"]
            scheduled_time = train["scheduledTime"].strftime("%H:%M")

            # If an estimate exists, display both values
            if train["liveEstimateTime"]:
                estimate_time = train["liveEstimateTime"].strftime("%H:%M")
                msg = "{} {} => {}".format(line_id, scheduled_time, estimate_time)

            else:
                msg = "{} {}".format(line_id, scheduled_time)

            if train["cancelled"]:
                msg = "CANCELLED"

            label.setText(msg)

        # Return a delay until the next departure: either the measured time
        # until the next departure or and upper/lower bound of 40min/12min
        if not trains:
            msec_until_next = 12*60*1000  # set a delay of 12 minutes if no trains received
        else:
            next_departure = trains[0]["scheduledTime"]
            msec_until_next = self.train_parser.msecs_until_datetime(next_departure)

        # pair the delay with the bounds, sort and return the middle value
        waits_with_bounds = sorted([12*60*1000, msec_until_next, 40*60*1000])
        return waits_with_bounds[1]

    def toggle_display_mode(self):
        """Change main window dispaly mode between fullscreen and normal
        depending on current its mode.
        """
        if self.main_window.windowState() == Qt.WindowFullScreen:
            self.main_window.showNormal()
        else:
            self.main_window.showFullScreen()
            # Keep the settings window active to prevent main window from
            # burying it
            self.settings_window.activateWindow()

    def blank_screen_and_hide_control_buttons(self):
        """Callback to turning the screen off: turn off backlight power and
        hide the main window's control buttons to prevent accidentally hitting
        them when the screen in blank.
        """
        rpi_utils.toggle_screen_state("off")
        self.hide_control_buttons()

    def enable_screen_and_show_control_buttons(self):
        """Callback to turning the screen on: re-enable backlight power and show
        the main window's control buttons.
        """
        rpi_utils.toggle_screen_state("on")
        self.show_control_buttons()

    def hide_control_buttons(self):
        """Hides the main window's bottom row buttons."""
        self.settings_button.hide()
        self.radio_button.hide()
        self.blank_button.hide()
        self.close_button.hide()

    def show_control_buttons(self):
        """Showes the main window's bottom row buttons."""
        self.settings_button.show()
        self.radio_button.show()
        self.blank_button.show()
        self.close_button.show()

    def enable_tts(self):
        """Callback to the checkbox enabling TTS feature: set the config
        to match the selected value.
        """
        state = "0"
        if self.settings_window.readaloud_checkbox.isChecked():
            state = "1"
        self.env.config.set("main", "readaloud", state)

    def enable_nightmode(self):
        """Callback to the checkbox enabling TTS feature: set the config
        to match the selected value.
        """
        state = "0"
        if self.settings_window.nightmode_checkbox.isChecked():
            state = self.original_nightmode_offset
        self.env.config.set("alarm", "nightmode_offset", state)

    def cleanup_and_exit(self):
        """Callback to the close button. Close any existing radio streams and the
        application itself.
        """
        self.radio.stop()
        QApplication.instance().quit()

    def debug_key_press_event(self, event):
        """Custom keyPressEvent handler for debuggin purposes: prints the current
        contents configuration.
        """
        if event.key() == Qt.Key_S:
            config = {section: dict(self.env.config[section])
                      for section in self.env.config.sections()}
            print(json.dumps(config, indent=4))


class AlarmPlayThread(QThread):
    signal = pyqtSignal(int)

    def __init__(self, env):
        super().__init__()
        self.env = env

    # run method gets called when we start the thread
    def run(self):
        alarm = alarm_builder.Alarm(self.env)
        alarm.sound_alarm_without_gui_or_radio()

        # inform the main thread that playing has finished
        self.signal.emit(1)


class RadioStreamer:
    """Helper class for playing a radio stream via mplayer."""

    def __init__(self):
        self.process = None

    def is_playing(self):
        """Check if mplayer is currently running. Return True if it is."""
        return self.process is not None

    def play(self, url):
        """Open a radio stream as a child process. The stream will continue to run
        in the background.
        """
        cmd = "/usr/bin/mplayer -quiet -nolirc -playlist {} -loop 3".format(url).split()
        # Run the command via Popen directly to open the stream as an independent child
        # process. This way we do not wait for the stream to finish.
        self.process = subprocess.Popen(cmd)

    def stop(self):
        """Terminate the running mplayer process."""
        try:
            self.process.terminate()
            self.process = None
        except AttributeError:
            return


class CronWriter:
    """Helper class for writes cron entries. Uses crontab via subprocess."""

    def __init__(self, config_file):
        # format absolute paths to alarm_builder.py and the config file
        self.path_to_alarm_runner = os.path.abspath("play_alarm.py")
        self.config_file = config_file

    def get_cron_lines(self):
        """Return crontab as list of lines."""
        crontab = subprocess.check_output(["crontab", "-l"]).decode()
        lines = crontab.split("\n")
        return lines

    def get_current_alarm(self):
        """Check if there's an alarm line in crontab and return it's time HH:MM format
        as well as the status (enabled / disabled). If no alarm set, returns empty
        string as time.
        If there are multiple lines in cron, only the first is processed.
        Return
            a tuple of (enabled, alarm time) where tuple is a boolean denoting whether
            the alarm has been commented out or not.
        """
        cron_lines = self.get_cron_lines()
        alarm_lines = [line for line in cron_lines if self.path_to_alarm_runner in line]

        if alarm_lines:
            line = alarm_lines[0]
            # strip comment symbol and whitespace from the start (if any)
            split = line.lstrip("# ").split()
            minute = split[0]
            hour = split[1]

            time = hour.zfill(2) + ":" + minute.zfill(2)
            enabled = "#" not in line

            return (enabled, time)

        return (False, "")

    def get_crontab_lines_without_alarm(self):
        """Return the crontab as a newline delimited list without alarm entries."""
        cron_lines = self.get_cron_lines()
        return [line for line in cron_lines if self.path_to_alarm_runner not in line]

    def disable_entry(self):
        """Comment out existing alarm entry in cron."""
        cron_lines = self.get_cron_lines()
        alarm_lines = [line for line in cron_lines if self.path_to_alarm_runner in line]

        if alarm_lines:
            line = alarm_lines[0]
            idx = cron_lines.index(line)

            # overwrite the original line
            if "#" not in line:
                disabled_line = "# " + line
                cron_lines[idx] = disabled_line

        # write as the new crontab
        self.write_crontab(cron_lines)

    def delete_entry(self):
        """Remove cron line matching alarm entry."""
        crontab_lines = self.get_crontab_lines_without_alarm()

        # Remove any extra empty lines from the end and keep just one
        crontab = "\n".join(crontab_lines).rstrip("\n")
        crontab += "\n"

        # write as the new crontab
        self.write_crontab(crontab)

    def create_entry(self, s):
        """Given a HH:MM string, format it a valid cron entry. Date part is set
        to *, ie. every day.
        """
        t = time.strptime(s, "%H:%M")

        entry = "{min} {hour} * * * {python_exec} {path_to_alarm_runner} {path_to_config}".format(
            min=t.tm_min,
            hour=t.tm_hour,
            python_exec=sys.executable,
            path_to_alarm_runner=self.path_to_alarm_runner,
            path_to_config=self.config_file
        )

        return entry

    def add_entry(self, entry):
        """Add an entry for alarm_builder.py. Existing crontab is overwritten."""
        crontab_lines = self.get_crontab_lines_without_alarm()

        # Add new entry and overwrite the crontab file
        crontab_lines.append(entry)
        crontab_lines.append("\n")  # need a newline at the end
        self.write_crontab(crontab_lines)

    def write_crontab(self, crontab):
        """Write crontab as the new crontab using subprocess. Argument may be a string
        or list of lines.
        """
        if isinstance(crontab, list):
            crontab = "\n".join(crontab)

        p = subprocess.Popen(["crontab", "-", crontab], stdin=subprocess.PIPE)
        p.communicate(input=crontab.encode("utf8"))
