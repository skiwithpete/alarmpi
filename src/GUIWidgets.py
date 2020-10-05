#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""PyQt5 QWidgets for main and settings windows."""


import time
from functools import partial
from collections import namedtuple

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QLCDNumber,
    QGridLayout,
    QSizePolicy,
    QDesktopWidget,
    QCheckBox,
    QComboBox
)

from src import utils



# Create namedtuples for storing button and label configurations
ButtonConfig = namedtuple("ButtonConfig", ["text", "position", "slot", "size_policy"])
ButtonConfig.__new__.__defaults__ = (
    None, None, None, (QSizePolicy.Preferred, QSizePolicy.Preferred))


class AlarmWindow(QWidget):
    """QWidget subclass for main window."""

    def __init__(self):
        super().__init__()
        self.control_buttons = {}  # setup a dict for tracking control buttons
        self.initUI()

    def initUI(self):
        # Setup base and subgrids for layouting
        base_layout = QGridLayout(self)
        alarm_grid = QGridLayout()
        left_grid = QGridLayout()
        right_grid = QGridLayout()
        bottom_grid = QGridLayout()

        with open("src/style.qss") as f:
            self.setStyleSheet(f.read())
        self.setAutoFillBackground(True)

        # ** Center grid: current and alarm time displays **
        # alarm_grid.setVerticalSpacing(0)
        self.clock_lcd = QLCDNumber(8, self)
        self.clock_lcd.setSegmentStyle(QLCDNumber.Flat)
        alarm_grid.addWidget(self.clock_lcd, 0, 0, 1, 1)

        self.setup_clock_polling()

        self.alarm_time_lcd = QLCDNumber(8, self)
        self.alarm_time_lcd.display("")
        self.alarm_time_lcd.setMinimumHeight(30)
        self.alarm_time_lcd.setSegmentStyle(QLCDNumber.Flat)
        alarm_grid.addWidget(self.alarm_time_lcd, 1, 0, 1, 1, Qt.AlignTop)

        # ** Bottom grid: main UI control buttons **
        button_configs = [
            ButtonConfig(text="Settings", position=(0, 0)),
            ButtonConfig(text="Blank", position=(0, 1)),
            ButtonConfig(text="Radio", position=(0, 2)),
            ButtonConfig(text="Close", position=(0, 3))
        ]

        bottom_grid.setSpacing(0)
        for config in button_configs:
            button = QPushButton(config.text, self)
            button.setSizePolicy(*config.size_policy)
            self.control_buttons[config.text] = button  # store a reference to the button

            if config.slot:
                button.clicked.connect(config.slot)
            bottom_grid.addWidget(button, *config.position)

        # ** Left grid: next 3 departing trains **
        self.train_labels = []
        for i in range(3):
            train_label = QLabel("", self)
            left_grid.addWidget(train_label, i, 0, Qt.AlignTop)
            self.train_labels.append(train_label)

        # Set a non zero strectfactor to the bottom rows of both side bars, so
        # the last item takes all the remaining space and all QLabels appear
        # on top of each other
        left_grid.setRowStretch(2, 1)
        right_grid.setRowStretch(2, 1)

        # ** Right grid: weather forecast **
        self.temperature_label = QLabel("", self)
        self.wind_speed_label = QLabel("", self)
        self.weather_container = QLabel(self)
        right_grid.addWidget(self.temperature_label, 0, 0, Qt.AlignRight)
        right_grid.addWidget(self.wind_speed_label, 1, 0, Qt.AlignRight)
        right_grid.addWidget(self.weather_container, 2, 0, Qt.AlignRight | Qt.AlignTop)

        base_layout.addLayout(alarm_grid, 0, 1)
        base_layout.addLayout(left_grid, 0, 0)
        base_layout.addLayout(right_grid, 0, 2)
        base_layout.addLayout(bottom_grid, 1, 0, 1, 3)

        # Set row strech so the bottom bar doesn't take too much vertical space
        base_layout.setRowStretch(0, 2)
        base_layout.setRowStretch(1, 1)

        self.setLayout(base_layout)
        self.resize(620, 420)
        self.center()

        self.setWindowTitle("Alarmpi")
        self.show()

    def setup_clock_polling(self):
        """Set the main LCD display to the current time and start polling for
        with 1 second intervals.
        """
        def tick():
            s = time.strftime("%H:%M:%S")
            self.clock_lcd.display(s)

        tick() # Call tick once to set the initial time 
        _timer = QTimer(self)
        _timer.timeout.connect(tick)
        _timer.start(1000)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class SettingsWindow(QWidget):
    ALARM_INPUT_ERROR = "ERROR: Invalid time"
    ALARM_INPUT_CLEAR = "Alarm cleared"
    ALARM_LABEL_EMPTY = "  :  "

    def __init__(self):
        super().__init__()
        self.control_buttons = {}
        self.numpad_buttons = {}
        self.initUI()

    def initUI(self):
        base_layout = QGridLayout()

        # subgrids for positioning elements
        left_grid = QGridLayout()
        right_grid = QGridLayout()
        bottom_grid = QGridLayout()

        # ** Right grid: numpad for settings the alarm **
        numpad_button_config = [
            ButtonConfig(text="1", position=(0, 0), slot=True),
            ButtonConfig(text="2", position=(0, 1), slot=True),
            ButtonConfig(text="3", position=(0, 2), slot=True),
            ButtonConfig(text="4", position=(1, 0), slot=True),
            ButtonConfig(text="5", position=(1, 1), slot=True),
            ButtonConfig(text="6", position=(1, 2), slot=True),
            ButtonConfig(text="7", position=(2, 0), slot=True),
            ButtonConfig(text="8", position=(2, 1), slot=True),
            ButtonConfig(text="9", position=(2, 2), slot=True),
            ButtonConfig(text="0", position=(3, 1), slot=True),
            ButtonConfig(text="set", position=(4, 0)),
            ButtonConfig(text="clear", position=(4, 2))
        ]

        for config in numpad_button_config:
            button = QPushButton(config.text, self)
            button.setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Expanding  # buttons should expand in vertical direction
            )

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
        self.input_alarm_time_label = QLabel(SettingsWindow.ALARM_LABEL_EMPTY, self)
        self.input_alarm_time_label.setAlignment(Qt.AlignCenter)
        right_grid.addWidget(self.input_alarm_time_label, 4, 1)

        # ** Bottom level main buttons **
        control_button_config = [
            ButtonConfig(text="Play now", position=(0, 0)),
            ButtonConfig(text="Toggle window", position=(0, 1)),
            ButtonConfig(text="Toggle brightness", position=(0, 2)),
            ButtonConfig(text="Close", position=(0, 3), slot=self.clear_labels_and_close)
        ]

        for config in control_button_config:
            button = QPushButton(config.text, self)
            button.setSizePolicy(*config.size_policy)
            self.control_buttons[config.text] = button

            if config.slot:
                button.clicked.connect(config.slot)
            bottom_grid.addWidget(button, *config.position)

        # ** Left grid: misc settings **
        settings_title = QLabel("Alarm settings", self)
        self.readaloud_checkbox = QCheckBox("Enable Text-to-Speech Alarm", self)
        self.nightmode_checkbox = QCheckBox("Enable Nightmode", self)
        self.alarm_brightness_checkbox = QCheckBox("Full Brightness on Alarm", self)

        # ComboBox for radio station, filled from 
        self.radio_station_combo_box = QComboBox(self)
        self.radio_station_combo_box.addItems(utils.RADIO_STATIONS)
        self.radio_station_combo_box.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding  # expand in vertical direction
        )

        self.alarm_time_status_label = QLabel(self)
        self.alarm_time_error_label = QLabel(self)
        self.alarm_time_error_label.setStyleSheet("color: #FF1414;")

        left_grid.addWidget(settings_title, 0, 0)
        left_grid.addWidget(self.readaloud_checkbox, 1, 0)
        left_grid.addWidget(self.nightmode_checkbox, 2, 0)
        left_grid.addWidget(self.alarm_brightness_checkbox, 3, 0)
        left_grid.addWidget(self.alarm_time_status_label, 4, 0)
        left_grid.addWidget(self.alarm_time_error_label, 5, 0)
        left_grid.addWidget(self.radio_station_combo_box, 6, 0)

        # Add grids to base layout
        base_layout.addLayout(left_grid, 0, 0)
        base_layout.addLayout(right_grid, 0, 1)
        base_layout.addLayout(bottom_grid, 1, 0, 1, 2)

        # Set stretch factors to rows so the button row doesn't take too much space
        base_layout.setRowStretch(0, 2)
        base_layout.setRowStretch(1, 1)

        self.setLayout(base_layout)
        self.resize(570, 420)
        self.center()

        self.setWindowTitle("Settings")

    def clear_labels_and_close(self):
        """Button handler for 'close' Button: clear any temporary status messages
        before closing the window.
        """
        if self.alarm_time_error_label.text() == SettingsWindow.ALARM_INPUT_ERROR:
            self.alarm_time_error_label.setText("")

        # Clear the status label if it not displaying a valid alarm time
        if self.alarm_time_status_label.text() == SettingsWindow.ALARM_INPUT_CLEAR:
            self.alarm_time_status_label.setText("")

        self.close()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_input_alarm_display(self, val):
        """Button handler for alarm input numpad. Updates the Label displaying
        the time corresponding to the input.
        Args:
            val (string): a single digit string to write as the next character
            to the label.
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
            new_value = list(val + SettingsWindow.ALARM_LABEL_EMPTY[1:])

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
            self.alarm_time_error_label.setText(SettingsWindow.ALARM_INPUT_ERROR)
            self.input_alarm_time_label.setText(SettingsWindow.ALARM_LABEL_EMPTY)
            return

    def clear_alarm(self):
        """Clear the time displayed on the alarm set label."""
        self.input_alarm_time_label.setText(SettingsWindow.ALARM_LABEL_EMPTY)
        self.alarm_time_status_label.setText(SettingsWindow.ALARM_INPUT_CLEAR)
        self.current_alarm_time = ""
        self.alarm_time_error_label.setText("")

    def set_alarm_input_success_message_with_time(self, time):
        """Helper function for setting the left pane alarm time info label."""
        msg = "Alarm set for {}".format(time)
        self.alarm_time_status_label.setText(msg)

    def set_alarm_input_time_label(self, time):
        """Helper function for setting the numpad label displaying selected time."""
        self.input_alarm_time_label.setText(time)
