#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""A PyQt5 clock radio application."""


import time
import datetime
import os
import sys
import subprocess
import signal
from functools import partial
from collections import namedtuple

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLCDNumber,
    QGridLayout,
    QApplication,
    QSizePolicy,
    QDesktopWidget
)
from PyQt5.QtGui import QPixmap

import alarmenv
import utils
import sound_the_alarm
from handlers import get_open_weather, get_train_arrivals

# Create namedtuples for storing button and label configurations
ButtonConfig = namedtuple("ButtonConfig", ["text", "position", "slot", "size_policy"])
ButtonConfig.__new__.__defaults__ = (
    None, None, None, (QSizePolicy.Preferred, QSizePolicy.Preferred))


class Clock:
    """Wrapper class for the clock itself. Defines interactions between
    UI elements and backend logic.
    """

    def __init__(self, config_file, **kwargs):
        self.main_window = AlarmWindow()
        self.settings_window = SettingsWindow()
        self.kwargs = kwargs

        # Read the alarm configuration file and initialize and alarmenv object
        self.config_file = config_file
        self.env = alarmenv.AlarmEnv(config_file)
        self.env.setup()

        self.cron = CronWriter(config_file)
        self.radio = RadioStreamer()
        self.alarm_player = sound_the_alarm.Alarm(self.env)

        section = self.env.get_section("openweathermap")
        self.weather_parser = get_open_weather.OpenWeatherMapClient(section)

        if kwargs["fullscreen"]:
            self.main_window.showFullScreen()

    def setup_button_handlers(self):
        # Setup references to main control buttons in both windows
        settings_button = self.main_window.control_buttons["Settings"]
        radio_button = self.main_window.control_buttons["Radio"]
        sleep_button = self.main_window.control_buttons["Sleep"]

        brightness_button = self.settings_window.control_buttons["Toggle brightness"]
        alarm_play_button = self.settings_window.control_buttons["Play now"]
        console_button = self.settings_window.control_buttons["Show console"]
        alarm_set_button = self.settings_window.numpad_buttons["set"]
        alarm_clear_button = self.settings_window.numpad_buttons["clear"]

        # Disable sleep button if host system is not a Raspberry Pi
        if not self.env.is_rpi:
            sleep_button.setEnabled(False)
            brightness_button.setEnabled(False)

        # Set main window's alarm time display to cron's time
        self.current_alarm_time = self.cron.get_current_alarm()
        self.main_window.alarm_time_lcd.display(self.current_alarm_time)

        self.main_window.mouseReleaseEvent = self.on_touch_event_handler
        signal.signal(signal.SIGUSR1, self.radio_signal_handler)
        signal.signal(signal.SIGUSR2, self.wakeup_signal_handler)

        self.setup_weather_polling()

        # Set button handlers for buttons requiring interactions between helper classes
        # ** main window buttons **
        settings_button.clicked.connect(self.settings_window.show)
        radio_button.clicked.connect(self.play_radio)
        sleep_button.clicked.connect(Clock.toggle_screensaver)

        # ** settings window buttons **
        brightness_button.clicked.connect(self.toggle_display_backlight_brightness)
        alarm_play_button.clicked.connect(self.alarm_player.sound_alarm_without_gui_or_radio)
        console_button.clicked.connect(self.main_window.showNormal)

        alarm_set_button.clicked.connect(self.set_alarm)
        alarm_clear_button.clicked.connect(self.clear_alarm)

    def radio_signal_handler(self, sig, frame):
        """Signal handler for incoming radio stream requests from sound_the_alarm.
        Opens the stream and sets radio button state as pressed.
        Also clears the main window's alarm display LCD widget if there is no alarm
        the next day.
        """
        self.play_radio()
        self.set_active_alarm_indicator()

    def wakeup_signal_handler(self, sig, frame):
        """Signal handler for waking up the screen. Sent by sound_the_alarm
        upon the alarm. If the screen is blank, reset the screensaver activated by xset.
        """
        self.toggle_screensaver("off")
        self.set_active_alarm_indicator()

    def on_touch_event_handler(self, event):
        print("foo")

    def set_alarm(self):
        """Handler to alarm set button in the settings window. Validates the
        time currently displaying and adds a cron entry. No alarm is set if
        value is invalid.
        """
        time_str = self.settings_window.validate_alarm_input()
        # if self.env.get_value("alarm", "include_weekends", fallback="0") == "1":
        if time_str:
            entry = self.cron.create_entry(time_str)
            self.cron.add_entry(entry)
            self.settings_window.alarm_input_label.setText(
                "Alarm set for {}".format(time_str))

            # update main window alarm display
            self.main_window.alarm_time_lcd.display(time_str)

        return

    def clear_alarm(self):
        """Handler for settings window's clear button: removes the cron entry
        and clears both window's alarm displays.
        """
        self.cron.delete_entry()
        self.settings_window.clear_alarm()
        self.main_window.alarm_time_lcd.display("")

    def set_screensaver_timeout(self):
        """Blank the screen after a short timeout if it is currently night time
        (ie. nightmode_offset hours before alarm time).
        """
        now = datetime.datetime.now()
        alarm_time = self.current_alarm_time  # HH:MM
        if not alarm_time:
            return

        try:
            offset = int(self.env.get_value("alarm", "nightmode_offset", fallback="0"))
            nighttime = utils.nighttime(now, offset, alarm_time)

            if nighttime:
                _timer = QTimer(self.main_window)
                _timer.setSingleShot(True)
                _timer.timeout.connect(Clock.toggle_screensaver)
                _timer.start(2*60*1000)  # 2 minute timeout until screen blank

        except ValueError:
            return

    def play_radio(self):
        """Callback to the 'Play radio' button: open or close the radio stream
        depending on the button state.
        """
        button = self.main_window.control_buttons["Radio"]

        button_checked = button.isChecked()
        if button_checked:
            self.radio.play(self.env.radio_url)
        else:
            self.radio.stop()

    def setup_weather_polling(self):
        # self.update_weather()
        _timer = QTimer(self.main_window)
        _timer.timeout.connect(self.update_weather)
        _timer.start(10*60*1000)  # 10 minute interval

    def update_weather(self):
        """Update the weather labels on the main window. Makes an API request
        openweathermap.org for current temperature and windspeed.
        """
        api_response = self.weather_parser.get_weather()
        weather = get_open_weather.OpenWeatherMapClient.format_response(api_response)

        temperature = weather["temp"]
        wind = weather["wind_speed_ms"]

        msg = "{}°C".format(round(temperature))
        self.main_window.temperature_label.setText(msg)

        msg = "{}m/s".format(round(wind))
        self.main_window.wind_speed_label.setText(msg)

    def toggle_display_backlight_brightness(self):
        """Reads Raspberry pi touch display's current brightness values from system
        file and sets it to either high or low depending on the current value.
        """
        PATH = "/sys/class/backlight/rpi_backlight/brightness"
        LOW = 9
        HIGH = 255

        with open(PATH) as f:
            brightness = int(f.read())

        # set to furthest away from current brightness
        if abs(brightness-LOW) < abs(brightness-HIGH):
            new_brightness = HIGH
        else:
            new_brightness = LOW

        with open(PATH, "w") as f:
            f.write(str(new_brightness))

    @staticmethod
    def toggle_screensaver(state="on"):
        """Use the xset utility to either activate the screen saver(the default)
        or turn it off. Touching the screen will also deactivate the screensaver.
        """
        cmd = "xset s reset".split()
        if state == "on":
            cmd = "xset s activate".split()

        # set required env variables so we don't need to run the whole command
        # with shell=True
        # Note: the user folder is assumed to be 'pi'
        # env = {"XAUTHORITY": "/home/pi/.Xauthority", "DISPLAY": ":0"}
        env = {"DISPLAY": ":0"}
        subprocess.run(cmd, env=env)


class AlarmWindow(QWidget):
    """QWidget subclass for main window."""

    def __init__(self):
        super().__init__()
        self.control_buttons = {}  # setup a dict for control buttons
        self.initUI()

    def initUI(self):
        # subgrids for layouting
        grid = QGridLayout()
        alarm_grid = QGridLayout()
        left_grid = QGridLayout()
        right_grid = QGridLayout()
        bottom_grid = QGridLayout()

        # ** Center grid: current and alarm time displays **
        self.clock_lcd = QLCDNumber(8, self)
        self.clock_lcd.setStyleSheet("border: 0px;")
        alarm_grid.addWidget(self.clock_lcd, 0, 0)

        self.tick()
        _timer = QTimer(self)
        _timer.timeout.connect(self.tick)
        _timer.start(1000)

        self.alarm_time_lcd = QLCDNumber(self)
        self.alarm_time_lcd.display("")
        self.alarm_time_lcd.setStyleSheet("border: 0px;")
        alarm_grid.addWidget(self.alarm_time_lcd, 1, 0)

        # ** Bottom grid: main UI control buttons **
        button_configs = [
            ButtonConfig(text="Settings", position=(0, 0)),
            ButtonConfig(text="Sleep", position=(0, 1)),
            ButtonConfig(text="Radio", position=(0, 2)),
            ButtonConfig(text="Close", position=(0, 3), slot=QApplication.instance().quit)
        ]

        for config in button_configs:
            button = QPushButton(config.text, self)
            button.setSizePolicy(*config.size_policy)
            self.control_buttons[config.text] = button  # store a reference to the button

            if config.slot:
                button.clicked.connect(config.slot)
            bottom_grid.addWidget(button, *config.position)

        # Set the Radio on/off button to a checkable button
        self.control_buttons["Radio"].setCheckable(True)

        # ** Left grid: next 3 departing trains **
        train1 = QLabel("U 6:54", self)
        train2 = QLabel("E 7:14", self)
        train3 = QLabel("U 7:33", self)
        left_grid.addWidget(train1, 0, 0)
        left_grid.addWidget(train2, 1, 0)
        left_grid.addWidget(train3, 2, 0)

        # ** Right grid: weather forecast **
        self.temperature_label = QLabel("16°C", self)
        self.wind_speed_label = QLabel("3m/s", self)

        weather_container = QLabel(self)
        pixmap = QPixmap('day_sunny_1-512.png').scaledToWidth(48)
        weather_container.setPixmap(pixmap)
        right_grid.addWidget(self.temperature_label, 0, 0, Qt.AlignRight)
        right_grid.addWidget(weather_container, 1, 0, Qt.AlignRight)
        right_grid.addWidget(self.wind_speed_label, 2, 0, Qt.AlignRight)

        grid.addLayout(alarm_grid, 0, 1)
        grid.addLayout(left_grid, 0, 0)
        grid.addLayout(right_grid, 0, 2)
        grid.addLayout(bottom_grid, 1, 0, 1, 3)

        # Set row strech so the bottom bar doesn't take too much space
        grid.setRowStretch(0, 2)
        grid.setRowStretch(1, 1)

        self.setLayout(grid)
        self.resize(600, 320)
        self.center()

        self.setWindowTitle("Alarmpi")
        self.show()

    def tick(self):
        s = time.strftime("%H:%M:%S")
        self.clock_lcd.display(s)

    def update_weather(self):
        pass

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.control_buttons = {}
        self.numpad_buttons = {}
        self.initUI()

    def initUI(self):
        grid = QGridLayout()

        # subgrids for positioning elements
        left_grid = QGridLayout()
        right_grid = QGridLayout()
        bottom_grid = QGridLayout()

        # ** Right grid: numpad for settings the alarm **
        instruction_label = QLabel("Set alarm HH:MM")
        right_grid.addWidget(instruction_label, 0, 0, 1, 3)

        numpad_button_config = [
            ButtonConfig(text="1", position=(1, 0), slot=True),
            ButtonConfig(text="2", position=(1, 1), slot=True),
            ButtonConfig(text="3", position=(1, 2), slot=True),
            ButtonConfig(text="4", position=(2, 0), slot=True),
            ButtonConfig(text="5", position=(2, 1), slot=True),
            ButtonConfig(text="6", position=(2, 2), slot=True),
            ButtonConfig(text="7", position=(3, 0), slot=True),
            ButtonConfig(text="8", position=(3, 1), slot=True),
            ButtonConfig(text="9", position=(3, 2), slot=True),
            ButtonConfig(text="0", position=(4, 1), slot=True),
            ButtonConfig(text="set", position=(5, 0)),
            ButtonConfig(text="clear", position=(5, 2))
        ]

        for config in numpad_button_config:
            button = QPushButton(config.text, self)

            if config.slot is True:
                # create a partial function with the button text to pass to
                # the handler
                slot = partial(self.update_input_alarm_display, config.text)
                button.clicked.connect(slot)
            else:
                self.numpad_buttons[config.text] = button
            right_grid.addWidget(button, *config.position)

        # Labels for displaying current active alarm time and time
        # set using the numpad controls.
        self.ALARM_LABEL_EMPTY = "  :  "
        self.input_alarm_time_label = QLabel(self.ALARM_LABEL_EMPTY)
        self.input_alarm_time_label.setAlignment(Qt.AlignCenter)
        right_grid.addWidget(self.input_alarm_time_label, 5, 1)

        self.alarm_input_label = QLabel("current alarm time: ")
        right_grid.addWidget(self.alarm_input_label, 6, 0, 1, 3)

        # ** Bottom level main buttons **
        control_button_config = [
            ButtonConfig(text="Play now", position=(0, 0)),
            ButtonConfig(text="Show console", position=(0, 1)),
            ButtonConfig(text="Toggle brightness", position=(0, 2)),
            ButtonConfig(text="Close", position=(0, 3), slot=self.close)
        ]

        for config in control_button_config:
            button = QPushButton(config.text, self)
            button.setSizePolicy(*config.size_policy)
            self.control_buttons[config.text] = button

            if config.slot:
                button.clicked.connect(config.slot)
            bottom_grid.addWidget(button, *config.position)

        # ** Left grid: misc settings **
        test_label = QLabel("foo", self)
        left_grid.addWidget(test_label, 1, 0)

        grid.addLayout(left_grid, 0, 0)
        grid.addLayout(right_grid, 0, 1)
        grid.addLayout(bottom_grid, 1, 0, 1, 2)

        self.setLayout(grid)
        self.resize(500, 300)
        self.center()

        self.setWindowTitle("Settings")

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_input_alarm_display(self, val):
        """Button handler for alarm input numpad. Updates the Label displaying
        the time corresponding to the input.
        """
        # Compute number of digits in the currently displayed value
        current_display_value = self.input_alarm_time_label.text()
        current_display_digits_num = sum(c.isdigit() for c in current_display_value)

        # The format for the alarm setup label is HH:MM. Depending on the length
        # of the currently displayed value either set the next digit or start
        # building a new value from the first digit.
        new_value = list(current_display_value)
        if current_display_digits_num < 2:
            new_value[current_display_digits_num] = val

        elif current_display_digits_num < 4:
            new_value[current_display_digits_num + 1] = val

        else:
            new_value = list(val + self.ALARM_LABEL_EMPTY[1:])

        new_value = "".join(new_value)
        self.input_alarm_time_label.setText(new_value)

    def validate_alarm_input(self):
        """Callback for "Set alarm" button: write a new cron entry for the alarm and
        display a message for the user. Existing cron alarms will be overwritten
        Invalid time values are not accepted.
        """
        try:
            entry_time = self.input_alarm_time_label.text()
            time.strptime(entry_time, "%H:%M")
            return entry_time
        except ValueError:
            self.alarm_input_label.setText("ERROR: Invalid time")
            return

    def clear_alarm(self):
        """Clear the time displayed on the alarm set label.
        """
        self.input_alarm_time_label.setText(self.ALARM_LABEL_EMPTY)
        self.alarm_input_label.setText("Alarm cleared")
        self.current_alarm_time = ""


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
        cmd = "/usr/bin/mplayer -quiet -nolirc -playlist {} -loop 0".format(url).split()
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
        self.config_file = config_file

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
