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

        # Setup a QTimer for the alarm
        self.alarm_timer = QTimer(self.main_window)
        self.alarm_timer.setSingleShot(True)
        self.alarm_timer.timeout.connect(self.play_alarm)

        #self.cron = CronWriter(config_file)
        radio_args = self.env.get_value("radio", "args")
        self.radio = RadioStreamer(radio_args)
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
            self.env.is_rpi = True  # fake Rpi environment so all buttons are enabled
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

        # Setup settings window's checkbox initial values:
        tts_enabled = self.env.config_has_match("main", "readaloud", "1")
        self.settings_window.readaloud_checkbox.setChecked(tts_enabled)

        # set nightmode as enabled if non zero offset specified in the config
        self.original_nightmode_offset = self.env.get_value(
            "alarm", "nightmode_offset", fallback="8")

        nightmode = (self.original_nightmode_offset != "0")
        self.settings_window.nightmode_checkbox.setChecked(nightmode)

        alarm_brightness_enabled = self.env.config_has_match("alarm", "set_brightness", "1")
        self.settings_window.alarm_brightness_checkbox.setChecked(alarm_brightness_enabled)

        # Setup signal handlers for alarm_builder.py signals
        signal.signal(signal.SIGUSR1, self.radio_signal_handler)
        signal.signal(signal.SIGUSR2, self.wakeup_signal_handler)

        # Set main window's alarm time display to cron's time
        self.current_alarm_time = self.get_current_alarm()
        if self.current_alarm_time:
            self.main_window.alarm_time_lcd.display(self.current_alarm_time)

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

        # Disable the radio button if radio is disabled in config
        if self.env.get_value("radio", "enabled") == "0":
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

        # Settings window checkbox callbacks
        self.settings_window.readaloud_checkbox.stateChanged.connect(self.enable_tts)
        self.settings_window.nightmode_checkbox.stateChanged.connect(self.enable_nightmode)
        self.settings_window.alarm_brightness_checkbox.stateChanged.connect(
            self.enable_alarm_brightness_change)

    def open_settings_window(self):
        """Callback for opening the settings window. Checks whether an alarm time should
        be displayed (ie. is there an alarm line in cron)
        Also clears timer for blanking the screen (if active).
        """
        self.current_alarm_time = self.get_current_alarm()

        # For active alarms, write time to left pane info label as well as to the
        # right pane numpad time label.
        if self.current_alarm_time:
            self.settings_window.set_alarm_input_success_message_with_time(self.current_alarm_time)
            self.settings_window.set_alarm_input_time_label(self.current_alarm_time)

        else:
            self.settings_window.alarm_time_status_label.setText("")
            self.settings_window.set_alarm_input_time_label(
                GUIWidgets.SettingsWindow.ALARM_LABEL_EMPTY)

        # Clear any screen blanking timer and display the window
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
        """Signal handler for waking up the screen: ensure the screen is enabled."""
        self.main_window.alarm_time_lcd.display("")

        if self.env.is_rpi:
            self.enable_screen_and_show_control_buttons()

            # Check if brightness should be set to full
            if self.env.config_has_match("alarm", "set_brightness", "1"):
                rpi_utils.set_display_backlight_brightness(rpi_utils.HIGH_BRIGHTNESS)

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
        time_str = self.settings_window.validate_alarm_input()
        if time_str:

            # Update displayed alarm time settings and main window
            self.main_window.alarm_time_lcd.display(time_str)
            self.settings_window.set_alarm_input_success_message_with_time(time_str)

            alarm_wait_ms = utils.time_str_to_msec_delta(time_str)
            self.alarm_timer.start(alarm_wait_ms)

            # Set screen brightness to low
            if self.env.config_has_match("alarm", "set_brightness", "1"):
                rpi_utils.set_display_backlight_brightness(rpi_utils.LOW_BRIGHTNESS)

    def clear_alarm(self):
        """Handler for settings window's 'clear' button. Stops any running
        alarm timers. Also clears both window's alarm displays.
        """
        self.alarm_timer.stop()
        self.settings_window.clear_alarm()
        self.main_window.alarm_time_lcd.display("")

    def get_current_alarm(self):
        """Check for existing running alarm timers and return alarm time in HH:MM format."""
        active = self.alarm_timer.isActive()
        if active:
            time_remaining = self.alarm_timer.remainingTime()
            alarm_time = utils.msec_to_time_str(time_remaining)

            return alarm_time

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

        # Set a new timeout for blanking the screen if nighttime
        if nighttime:
            self.screen_blank_timer.start(3*1000)  # 3 second timer

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
            self.radio.play()
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
        """Update the weather labels on the main window. Makes an API request to
        openweathermap.org for current temperature and windspeed.
        """
        logging.info("Updating weather")
        weather = self.weather_parser.fetch_and_format_weather()

        temperature = weather["temp"]
        wind = weather["wind_speed_ms"]

        try:
            msg = "{}°C".format(round(temperature))
            self.main_window.temperature_label.setText(msg)

            msg = "{}m/s".format(round(wind))
            self.main_window.wind_speed_label.setText(msg)

            icon_id = weather["icon"]
            icon_binary = get_open_weather.OpenWeatherMapClient.get_weather_icon(icon_id)

            pixmap = QPixmap()
            pixmap.loadFromData(icon_binary)
            self.main_window.weather_container.setPixmap(pixmap)

        except TypeError: # raised if weather is an an error template
            self.main_window.temperature_label.setText("ERR")
            self.main_window.wind_speed_label.setText("ERR")


    def setup_train_polling(self):
        """Setup polling for next train departure times every 12 minutes."""
        self.update_trains()
        _timer = QTimer(self.main_window)
        _timer.timeout.connect(self.update_trains)
        _timer.start(5*60*1000)

    def update_trains(self):
        """Fetch new train data from DigiTraffic API and display on the right sidebar."""
        logging.info("Updating trains")
        trains = self.train_parser.run()

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
                msg = "{} {} CANCELLED".format(line_id, scheduled_time)

            label.setText(msg)

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

    def enable_alarm_brightness_change(self):
        """Callback to the checkbox enabling brightness change on alarm: set the config
        to match the selected value.
        """
        state = "0"
        if self.settings_window.alarm_brightness_checkbox.isChecked():
            state = "1"
        self.env.config.set("alarm", "set_brightness", state)

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
    def __init__(self, args):
        self.process = None
        self.args = args

    def is_playing(self):
        """Check if mplayer is currently running. Return True if it is."""
        return self.process is not None

    def play(self):
        """Open a radio stream as a child process. The stream will continue to run
        in the background.
        """
        cmd = "/usr/bin/mplayer {}".format(self.args).split()
        # Run the command via Popen directly to open the stream as an independent child
        # process. This way we do not wait for the stream to finish.
        # Output is captured to file.

        with open("logs/radio.log", "w") as f:
            self.process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)

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

        # Remove trailing empty lines for easier processing, conversely an empty line
        # will be added in write_crontab
        while lines[-1] == "":
            lines.pop() 
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
        """Comment out existing alarm entry in crontab."""
        cron_lines = self.get_cron_lines()
        alarm_lines = [line for line in cron_lines if self.path_to_alarm_runner in line]

        if alarm_lines:
            line = alarm_lines[0]
            idx = cron_lines.index(line)

            # if the current alarm line is not commented out prepend it with
            # a '#' symbol and overwrite the original line
            if "#" not in line:
                disabled_line = "# " + line
                cron_lines[idx] = disabled_line

                # write as the new crontab
                self.write_crontab(cron_lines)

    def delete_entry(self):
        """Remove cron line matching alarm entry."""
        crontab_lines = self.get_crontab_lines_without_alarm()
        self.write_crontab(crontab_lines)

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
        self.write_crontab(crontab_lines)

    def write_crontab(self, crontab_lines):
        """Write crontab_lines as the new crontab using subprocess. Argument should be
        a list of lines
        """
        # Ensure crontab ends with a single empty line
        if crontab_lines[-1] != "":
            crontab_lines.append("")

        crontab = "\n".join(crontab_lines)

        p = subprocess.Popen(["crontab", "-", crontab], stdin=subprocess.PIPE)
        p.communicate(input=crontab.encode("utf8"))
