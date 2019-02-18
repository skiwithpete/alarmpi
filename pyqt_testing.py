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

import sys
import time
from collections import namedtuple

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QLCDNumber,
    QTextEdit,
    QGridLayout,
    QApplication,
    QSizePolicy,
    QDialog,
    QDesktopWidget,
    QMainWindow
)
from PyQt5.QtGui import QPixmap


# Create namedtuples for storing button and label configurations
ButtonConfig = namedtuple("ButtonConfig", ["text", "position", "slot", "size_policy"])
ButtonConfig.__new__.__defaults__ = (
    None, None, None, (QSizePolicy.Preferred, QSizePolicy.Preferred))


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.settings_window = SettingsWindow()
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
        self.tick()
        self.clock_lcd.setStyleSheet("border: 0px;")
        alarm_grid.addWidget(self.clock_lcd, 0, 0)

        _timer = QTimer(self)
        _timer.timeout.connect(self.tick)
        _timer.start(1000)

        alarm_time_lcd = QLCDNumber(self)
        alarm_time_lcd.display("7:15")
        alarm_time_lcd.setStyleSheet("border: 0px;")
        alarm_grid.addWidget(alarm_time_lcd, 1, 0)

        # ** Bottom grid: main UI control buttons **
        button_configs = [
            ButtonConfig(text="Settings", position=(0, 0), slot=self.settings_window.initUI),
            ButtonConfig(text="Sleep", position=(0, 1)),
            ButtonConfig(text="Radio", position=(0, 2)),
            ButtonConfig(text="Close", position=(0, 3), slot=QApplication.instance().quit)
        ]

        for config in button_configs:
            button = QPushButton(config.text, self)
            button.setSizePolicy(*config.size_policy)

            if config.slot:
                button.clicked.connect(config.slot)
            bottom_grid.addWidget(button, *config.position)

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

        self.setWindowTitle('Review')
        self.show()

    def tick(self):
        s = time.strftime("%H:%M:%S")
        self.clock_lcd.display(s)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


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
            ButtonConfig(text="Close", position=(0, 2), slot=self.close)
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
