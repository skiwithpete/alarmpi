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

import alarmenv
import utils
import sound_the_alarm
import GUIWidgets
import rpi_utils
from handlers import get_open_weather, get_next_trains


class Clock:
    """Wrapper class for the clock itself. Defines interactions between
    UI elements and backend logic.
    """

    def __init__(self, config_file, **kwargs):
        self.main_window = GUIWidgets.AlarmWindow()
        self.settings_window = GUIWidgets.SettingsWindow()

        # Read the alarm configuration file and initialize and alarmenv object
        self.config_file = config_file
        self.env = alarmenv.AlarmEnv(config_file)
        self.env.setup()

        self.cron = CronWriter(config_file)
        self.radio = RadioStreamer()
        self.alarm_player = sound_the_alarm.Alarm(self.env)
        self.train_parser = get_next_trains.TrainParser()

        section = self.env.get_section("openweathermap")
        self.weather_parser = get_open_weather.OpenWeatherMapClient(section)

        if kwargs["fullscreen"]:
            self.main_window.showFullScreen()
            self.main_window.setCursor(Qt.BlankCursor)
            self.settings_window.setCursor(Qt.BlankCursor)

        if kwargs["debug"]:
            self.env.config.set("polling", "weather", "0")
            self.env.config.set("polling", "train", "0")
            self.main_window.keyPressEvent = self.debug_key_press_event

    def setup(self):
        """Setup various button handlers as well as weather and train data polling
        for the main windows side bar.
        """
        self.setup_button_handlers()

        # TODO check for an API key
        if self.env.get_value("polling", "weather", fallback=False) == "1":
            self.setup_weather_polling()

        if self.env.get_value("polling", "train", fallback=False) == "1":
            self.setup_train_polling()

        # Setup settings window's checkboxes:
        # set initial values to config values and set handlers
        tts_enabled = self.env.config_has_match("main", "readaloud", "1")
        self.settings_window.readaloud_checkbox.setChecked(tts_enabled)
        weekends = self.env.config_has_match("alarm", "include_weekends", "1")
        self.settings_window.weekend_checkbox.setChecked(weekends)

        # set nightmode as enabled if non zero offset specified in the config
        self.original_nightmode_offset = self.env.get_value(
            "alarm", "nightmode_offset", fallback="8")

        nightmode = (self.original_nightmode_offset != "0")
        self.settings_window.nightmode_checkbox.setChecked(nightmode)

        signal.signal(signal.SIGUSR1, self.radio_signal_handler)
        signal.signal(signal.SIGUSR2, self.wakeup_signal_handler)

        # Set main window's alarm time display to cron's time
        self.current_alarm_time = self.cron.get_current_alarm()
        self.main_window.alarm_time_lcd.display(self.current_alarm_time)

        # Also set the setting's window alarm time label
        msg = "current alarm time: {}".format(self.current_alarm_time)
        self.settings_window.alarm_time_status_label.setText(msg)

        self.screen_blank_timer = QTimer(self.main_window)
        self.screen_blank_timer.setSingleShot(True)
        self.screen_blank_timer.timeout.connect(lambda: rpi_utils.toggle_screen_state("off"))

        self.main_window.mouseReleaseEvent = self.on_release_event_handler

    def setup_button_handlers(self):
        """Setup button handlers for the main window and settings window."""
        # Setup references to main control buttons in both windows
        settings_button = self.main_window.control_buttons["Settings"]
        radio_button = self.main_window.control_buttons["Radio"]
        blank_button = self.main_window.control_buttons["Blank"]
        close_button = self.main_window.control_buttons["Close"]

        brightness_button = self.settings_window.control_buttons["Toggle brightness"]
        alarm_play_button = self.settings_window.control_buttons["Play now"]
        window_button = self.settings_window.control_buttons["Toggle window"]
        alarm_set_button = self.settings_window.numpad_buttons["set"]
        alarm_clear_button = self.settings_window.numpad_buttons["clear"]

        # Disable blank and brightness buttons if host system is not a Raspberry Pi
        if not self.env.is_rpi:
            blank_button.setEnabled(False)
            brightness_button.setEnabled(False)

        # Set button handlers for buttons requiring interactions between helper classes
        # ** main window buttons **
        settings_button.clicked.connect(self.open_settings_window)
        radio_button.setCheckable(True)  # Set the Radio on/off button to a checkable button
        radio_button.clicked.connect(self.play_radio)
        blank_button.clicked.connect(lambda: rpi_utils.toggle_screen_state("off"))
        close_button.clicked.connect(self.cleanup_and_exit)

        # ** settings window buttons **
        brightness_button.clicked.connect(rpi_utils.toggle_display_backlight_brightness)
        #alarm_play_thread = AlarmPlayThread(self.alarm_player.sound_alarm_without_gui_or_radio)
        alarm_play_button.clicked.connect(self.alarm_player.sound_alarm_without_gui_or_radio)

        window_button.clicked.connect(self.toggle_display_mode)
        alarm_set_button.clicked.connect(self.set_alarm)
        alarm_clear_button.clicked.connect(self.clear_alarm)

        # Settings window checkboxes
        self.settings_window.readaloud_checkbox.stateChanged.connect(self.enable_tts)
        self.settings_window.weekend_checkbox.stateChanged.connect(self.enable_weekends)
        self.settings_window.nightmode_checkbox.stateChanged.connect(self.enable_nightmode)

    def open_settings_window(self):
        """Callback for opening the settings window. Also clears timer for blanking
        the screen (if active).
        """
        self.screen_blank_timer.stop()
        self.settings_window.show()

    def radio_signal_handler(self, sig, frame):
        """Signal handler for incoming radio stream requests from sound_the_alarm.
        Opens the stream and sets radio button state as pressed.
        Also clears the main window's alarm display LCD widget if there is no alarm
        the next day.
        """
        self.main_window.control_buttons["Radio"].click()  # emit a click signal
        self.set_active_alarm_indicator()

    def wakeup_signal_handler(self, sig, frame):
        """Signal handler for waking up the screen."""
        rpi_utils.toggle_screen_state("on")
        self.set_active_alarm_indicator()

    def on_release_event_handler(self, event):
        print("clicked")
        # get screen state before the event
        old_screen_state_powered = rpi_utils.screen_is_powered()

        rpi_utils.toggle_screen_state("on")
        self.set_active_alarm_indicator()

        # set screen blanking timeout if the screen was blank before the event
        if not old_screen_state_powered:
            self.set_screen_blank_timeout()

    def set_alarm(self):
        """Handler for settings window's 'set' button. Validates the suer selected
        time and adds a cron entry (if valid). No alarm is set if value is invalid.
        """
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
        next_departure = trains[0]["scheduledTime"]
        msec_until_next = self.train_parser.msecs_until_datetime(next_departure)

        # pair the measured delay with the bounds, sort and return the middle value
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

    def set_active_alarm_indicator(self):
        """Updates the main window label displaying set alarm time. By default the
        alarm only plays on weekdays. If so, empty the label after friday's alarm.
        """
        # Do nothing if alarm plays on weekends
        if self.env.get_value("alarm", "include_weekends", fallback="0") == "1":
            return

        # Do nothing if no alarm set
        alarm_time = self.current_alarm_time  # string: HH:MM
        if not alarm_time:
            return

        # Weekend detection: is current date between friday's alarm and
        # nightmode_offset before monday's alarm
        now = datetime.datetime.now()
        offset = int(self.env.get_value("alarm", "nightmode_offset", fallback="0"))
        weekend = utils.weekend(now, offset, alarm_time)
        if weekend:
            self.main_window.alarm_time_lcd.display("")
        else:
            self.main_window.alarm_time_lcd.display(alarm_time)

    def enable_tts(self):
        """Callback to the checkbox enabling TTS feature: set the config
        to match the selected value.
        """
        state = "0"
        if self.settings_window.readaloud_checkbox.isChecked():
            state = "1"
        self.env.config.set("main", "readaloud", state)

    def enable_weekends(self):
        """Callback to the checkbox enabling TTS feature: set the config
        to match the selected value.
        """
        state = "0"
        if self.settings_window.weekend_checkbox.isChecked():
            state = "1"
        self.env.config.set("alarm", "include_weekends", state)

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
    signal = pyqtSignal("PyQt_PyObject")

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    # run method gets called when we start the thread
    def run(self):
        self.callback()


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
        # format absolute paths to sound_the_alarm.py and the config file
        self.path_to_alarm = os.path.abspath("sound_the_alarm.py")
        self.config_file = os.path.abspath(config_file)

    def get_crontab(self):
        """Return the current crontab"""
        # check_output returns a byte string
        return subprocess.check_output(["crontab", "-l"]).decode()

    def get_current_alarm(self):
        """If an alarm has been set, return its time in HH:MM format. If not set
        returns an empty string.
        """
        crontab = subprocess.check_output(["crontab", "-l"]).decode()
        lines = crontab.split("\n")
        alarm_line = [line for line in lines if self.path_to_alarm in line]

        if alarm_line:
            split = alarm_line[0].split()
            minute = split[0]
            hour = split[1]

            return hour.zfill(2) + ":" + minute.zfill(2)

        return ""

    def get_crontab_lines_without_alarm(self):
        """Return the crontab as a newline delimited list without alarm entries."""
        # check_output returns a byte string
        crontab = subprocess.check_output(["crontab", "-l"]).decode()
        crontab_lines = crontab.split("\n")

        return [line for line in crontab_lines if self.path_to_alarm not in line]

    def delete_entry(self):
        """Delete cron entry for sound_the_alarm.py."""
        crontab_lines = self.get_crontab_lines_without_alarm()

        # Remove any extra empty lines from the end and keep just one
        crontab = "\n".join(crontab_lines).rstrip("\n")
        crontab += "\n"

        # write as the new crontab
        self.write_crontab(crontab)

    def create_entry(self, s, include_weekends=False):
        """Given a HH:MM string, format it a valid cron entry."""
        t = time.strptime(s, "%H:%M")

        date_range = "1-5"
        if include_weekends:
            date_range = "*"

        entry = "{min} {hour} * * {date_range} {python_exec} {path_to_alarm} {path_to_config}".format(
            min=t.tm_min,
            hour=t.tm_hour,
            date_range=date_range,
            python_exec=sys.executable,
            path_to_alarm=self.path_to_alarm,
            path_to_config=self.config_file
        )

        return entry

    def add_entry(self, entry):
        """Add an entry for sound_the_alarm.py. Existing crontab is overwritten."""
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
