#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial

In this example, we create a bit
more complicated window layout using
the QGridLayout manager.

author: Jan Bodnar
website: zetcode.com
last edited: January 2015
"""


import time
import datetime
import os
import subprocess
import signal
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

# Create namedtuples for storing button and label configurations
ButtonConfig = namedtuple("ButtonConfig", ["text", "position", "slot", "size_policy"])
ButtonConfig.__new__.__defaults__ = (
    None, None, None, (QSizePolicy.Preferred, QSizePolicy.Preferred))


class AlarmWindow(QWidget):
    """QWidget subclass for main window."""

    def __init__(self, config_file, **kwargs):
        super().__init__()
        self.settings_window = SettingsWindow()
        self.initUI()

        self.cron = CronWriter()

        # Read the alarm configuration file and initialize and alarmenv object
        self.config_file = config_file
        self.env = alarmenv.AlarmEnv(config_file)
        self.env.setup()

        # Disable sleep button if host system is not a Raspberry Pi
        if not self.env.is_rpi:
            self.control_buttons["Sleep"].setEnabled(False)

        self.radio = RadioStreamer()
        self.kwargs = kwargs

        self.current_alarm_time = self.cron.get_current_alarm()
        self.alarm_time_lcd.display(self.current_alarm_time)

        # Current active alarm display should be cleared if no active alarm
        # for the next day and re-set if alarm is active the next day
        # (ie. don't show alarm as active during weekends)
        # Add bindings for clearing and setting the active alarm label.
        #self.root.bind("<Button-1>", self.update_on_touch_tasks)
        #signal.signal(signal.SIGUSR1, self.radio_signal_handler)
        #signal.signal(signal.SIGUSR2, self.wakeup_signal_handler)

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
        self.alarm_time_lcd.display("0:00")
        self.alarm_time_lcd.setStyleSheet("border: 0px;")
        alarm_grid.addWidget(self.alarm_time_lcd, 1, 0)

        # ** Bottom grid: main UI control buttons **
        button_configs = [
            ButtonConfig(text="Settings", position=(0, 0), slot=self.settings_window.initUI),
            ButtonConfig(text="Sleep", position=(0, 1), slot=AlarmWindow.set_screensaver),
            ButtonConfig(text="Radio", position=(0, 2), slot=self.play_radio),
            ButtonConfig(text="Close", position=(0, 3), slot=QApplication.instance().quit)
        ]

        self.control_buttons = {}
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
        temperature = QLabel("16°", self)
        weather_container = QLabel(self)
        pixmap = QPixmap('day_sunny_1-512.png').scaledToWidth(48)
        weather_container.setPixmap(pixmap)
        right_grid.addWidget(temperature, 0, 0, Qt.AlignRight)
        right_grid.addWidget(weather_container, 0, 1, Qt.AlignRight)

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

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def radio_signal_handler(self, sig, frame):
        """Signal handler for incoming radio stream requests. Used to receive SIGUSR1
        signals from sound_the_alarm denoting a request to open a radio stream and to
        set the radio button as pressed. Also runs a check to see whether the displayed
        alarm time in the main window should be hidden (ie. no alarm the next day)."""
        self.play_radio()
        self.set_active_alarm_indicator()

    def wakeup_signal_handler(self, sig, frame):
        """Signal handler for waking up the screen. Sent by sound_the_alarm
        upon the alarm. If the screen is blank, reset the screensaver activated by xset."""
        self.set_screensaver("off")
        self.set_active_alarm_indicator()

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
                self.root.after(2000, AlarmWindow.set_screensaver, "on")
        except ValueError:
            return

    def play_radio(self):
        """Callback to the 'Play radio' button: open or close the radio stream
        depending on the button state.
        """
        # Change the relief of the button
        button = self.control_buttons["Radio"]

        # Get the current state of the button. Note that this function runs after
        # the click event. Ie. pressing isChecked returns True when the button
        # was activated and thus when the radio should be played.
        button_checked = button.isChecked()
        if button_checked:
            self.radio.play(self.env.radio_url)
        else:
            self.radio.stop()

    def change_display_backlight_brightness(self):
        """Reads Raspberry pi touch display's current brightness values from
        file and sets it either high or low depending on the current value.
        """
        PATH = "/sys/class/backlight/rpi_backlight/brightness"
        LOW = 9
        HIGH = 255

        with open(PATH) as f:
            brightness = int(f.read())

        # set to furthest away from current brightness
        if abs(brightness-LOW) < abs(brightness-HIGH):
            new_brightness = HIGH
            # also force button state to NORMAL similar to play_radio above
            self.brightness_button.config(state=tk.NORMAL)
        else:
            new_brightness = LOW

        with open(PATH, "w") as f:
            f.write(str(new_brightness))

    @staticmethod
    def set_screensaver(state="on"):
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


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

    def initUI(self):
        grid = QGridLayout()

        # subgrids for positioning elements
        left_grid = QGridLayout()
        right_grid = QGridLayout()
        bottom_grid = QGridLayout()

        # ** Right grid: numpad for settings the alarm **
        button_configs = [
            ButtonConfig(text="m/h", position=(0, 2)),
            ButtonConfig(text="1", position=(1, 0)),
            ButtonConfig(text="2", position=(1, 1)),
            ButtonConfig(text="3", position=(1, 2)),
            ButtonConfig(text="4", position=(2, 0)),
            ButtonConfig(text="5", position=(2, 1)),
            ButtonConfig(text="6", position=(2, 2)),
            ButtonConfig(text="7", position=(3, 0)),
            ButtonConfig(text="8", position=(3, 1)),
            ButtonConfig(text="9", position=(3, 2)),
            ButtonConfig(text="0", position=(4, 1)),
            ButtonConfig(text="set", position=(5, 0)),
            ButtonConfig(text="set", position=(5, 2)),
        ]

        for config in button_configs:
            button = QPushButton(config.text, self)

            if config.slot:
                button.clicked.connect(config.slot)
            right_grid.addWidget(button, *config.position)

        # ** Bottom level main buttons **
        button_config = [
            ButtonConfig(text="Play now", position=(0, 0)),
            ButtonConfig(text="Show console", position=(0, 1)),
            ButtonConfig(text="Set brightness", position=(0, 2)),
            ButtonConfig(text="Close", position=(0, 3), slot=self.close)
        ]

        for config in button_config:
            button = QPushButton(config.text, self)
            button.setSizePolicy(*config.size_policy)

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
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


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

    def __init__(self):
        # format absolute paths to sound_the_alarm.py and the config file
        self.alarm_path = os.path.abspath("sound_the_alarm.py")

    def get_crontab(self):
        """Return the current crontab"""
        # check_output returns a byte string
        return subprocess.check_output(["crontab", "-l"]).decode()

    def get_current_alarm(self):
        """If an alarm has been set, return its time in HH: MM format. If not set
        returns an empty string.
        """
        crontab = subprocess.check_output(["crontab", "-l"]).decode()
        lines = crontab.split("\n")
        alarm_line = [line for line in lines if self.alarm_path in line]

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

        return [line for line in crontab_lines if self.alarm_path not in line]

    def delete_cron_entry(self):
        """Delete cron entry for sound_the_alarm.py."""
        crontab_lines = self.get_crontab_lines_without_alarm()

        # Remove any extra empty lines from the end and keep just one
        crontab = "\n".join(crontab_lines).rstrip("\n")
        crontab += "\n"

        # write as the new crontab
        self.write_crontab(crontab)

    def add_cron_entry(self, entry):
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
