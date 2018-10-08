#!/usr/bin/env python

"""
A Tkinter app displaying the current time and for setting up an alarm via a
cron entry.
"""

import time
import sys
import os
import subprocess
import tkinter as tk

from PIL import Image, ImageTk


class Clock:

    def __init__(self):
        """Create the root window for displaying time."""
        RED = "#FF1414"
        BLACK = "#090201"

        self.cron = CronWriter()
        self.current_alarm = self.cron.get_current_alarm()

        self.root = tk.Tk()
        self.format_window(self.root, dimensions=(600, 320), title="Clock", bg=BLACK)
        # self.root.resizable(0, 0) #Don't allow resizing

        # set row and column weights so widgets expand to all available space
        for x in range(2):
            tk.Grid.columnconfigure(self.root, x, weight=1)

        for y in range(3):
            tk.Grid.rowconfigure(self.root, y, weight=1)

        # Row 0: label for displaying current time
        self.clock_label = tk.Label(self.root, font=("times", 46, "bold"), fg=RED, bg=BLACK)
        self.clock_label.grid(row=0, column=0, ipadx=50, columnspan=2, rowspan=1,
                              sticky="sew")

        # Row 1: label for alarm time (if set)
        self.root_alarm_time_container = tk.StringVar()
        self.root_alarm_time_container.set(self.current_alarm)
        alarm_time_label = tk.Label(
            self.root, font=("times", 18, "bold"), textvariable=self.root_alarm_time_container, fg=RED, bg=BLACK)
        alarm_time_label.grid(row=1, column=0, columnspan=2, sticky="new")

        # Row 2: buttons for setting the alarm and exiting
        tk.Button(self.root, text="Set alarm",
                  command=self.open_alarm_window).grid(row=2, column=0, sticky="nsew")

        tk.Button(self.root, text="Close",
                  command=self.root.destroy).grid(row=2, column=1, sticky="nsew")

        self.tick()

    def tick(self):
        """Update the current time value every 1 second."""
        s = time.strftime('%H:%M:%S')
        if s != self.clock_label["text"]:
            self.clock_label["text"] = s
        self.clock_label.after(1000, self.tick)

    def open_alarm_window(self):
        """Create a new window for scheduling the alarm.
        rows: 4 columns: 7
        """
        top = tk.Toplevel()
        self.format_window(top, dimensions=(500, 230), title="Set alarm")

        # set weights to ensure widgets take free space within their cells
        for x in range(7):
            tk.Grid.columnconfigure(top, x, weight=1)

        for y in range(5):
            tk.Grid.rowconfigure(top, y, weight=1)

        # hour selectors on the left side of the window (rows 0-2, columns 0-2)
        hour_indicators = []
        tk.Label(top, text="Hour").grid(row=0, column=0, columnspan=3)
        for i in range(5):
            var = tk.IntVar()
            hour_indicators.append(var)
            button_value = 2**i

            padx = (0, 0)
            # the leftmost buttons should have a positive left padding
            if i % 3 == 0:
                padx = (10, 0)

            # first 3 buttons in consecutive columns on row 1, remaining 2 on row 2
            row = 1
            column = i % 3
            if i > 2:
                row = 2

            hour_button = tk.Checkbutton(
                top,
                text=str(button_value),
                variable=var,
                onvalue=button_value,
                offvalue=-button_value,
                indicatoron=False,
                command=lambda var=var: self.update_alarm_display_time("hour", var.get())
            )
            hour_button.grid(row=row, column=column, padx=padx, sticky="nsew")

        # label for showing the alarm time between the hour and minute selectors
        self.alarm_time_container = tk.StringVar()
        self.alarm_time_container.set("00:00")
        tk.Label(top, textvariable=self.alarm_time_container).grid(row=1, column=3)

        # label for displaying status messages upon setting the alarm
        self.alarm_status_container = tk.StringVar()
        tk.Label(top, textvariable=self.alarm_status_container).grid(row=2, column=3)

        image = Image.open("resources/alarm-1673577_640.png")
        image = image.resize((28, 28), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)

        self.alarm_indicator = tk.Label(top, image=photo)
        self.alarm_indicator.image = photo  # keep a reference!

        # check for existing alarm in cron and set indicator to main window
        if self.current_alarm:
            self.set_alarm_status_message(self.current_alarm)

        # minute selectors on the right (rows 0-2, columns 4-6)
        tk.Label(top, text="Minute").grid(row=0, column=4, columnspan=3)
        for i in range(6):
            var = tk.IntVar()
            button_value = 2**i

            padx = (0, 0)
            # padding for rightmost buttons
            if i % 3 == 2:
                padx = (0, 10)

            # first 3 buttons in consecutive columns on row 1, remaining 3 on row 2
            row = 1
            column = (i % 3) + 4
            if i > 2:
                row = 2

            hour_button = tk.Checkbutton(
                top,
                text=str(button_value),
                variable=var,
                onvalue=button_value,
                offvalue=-button_value,
                indicatoron=False,
                command=lambda var=var: self.update_alarm_display_time("minute", var.get())
            )
            hour_button.var = var
            hour_button.grid(row=row, column=column, padx=padx, sticky="nsew")

        # row 3  buttons for setting and clearing the alarm and exiting
        tk.Button(top, text="Set alarm", command=self.set_alarm).grid(
            row=3, column=0, rowspan=2, columnspan=2, pady=(10, 0), sticky="nsew")
        tk.Button(top, text="Clear alarm", command=self.clear_alarm).grid(
            row=3, column=2, rowspan=2, columnspan=3, pady=(10, 0), sticky="nsew")
        tk.Button(top, text="Close", command=top.destroy).grid(
            row=3, column=5, rowspan=2, columnspan=2, pady=(10, 0), sticky="nsew")

    def update_alarm_display_time(self, type_, value):
        """Given a type and a value update the alarm time label in the "set alarm" window.
        Args:
            type (string): Either 'hour' or 'minute'. Determines the part of the time to update.
            value (int): The value to add to existing hour or minute part of the alarm time.
        """
        old_alarm_time = self.alarm_time_container.get()
        hour = int(old_alarm_time.split(":")[0])
        minute = int(old_alarm_time.split(":")[1])

        if type_ == "hour":
            new_hour = hour + value
            new_value = str(new_hour).zfill(2) + ":" + str(minute).zfill(2)

        else:
            new_minute = minute + value
            new_value = str(hour).zfill(2) + ":" + str(new_minute).zfill(2)

        self.alarm_time_container.set(new_value)

    def set_alarm(self):
        """Callback for "Set alarm" button: add a new cron entry for alarm and
        display a message for the user. Existing cron alarms will be overwritten.
        """
        try:
            entry_time = self.alarm_time_container.get()
            t = time.strptime(entry_time, "%H:%M")
        except ValueError:
            self.alarm_status_container.set("Invalid time")
            return

        # define a cron entry with absolute paths to the executable and alarm script
        entry = "{min} {hour} * * 1-5 {python_exec} {path_to_alarm} {path_to_config}".format(
            hour=t.tm_hour,
            min=t.tm_min,
            python_exec=sys.executable,
            path_to_alarm=self.cron.alarm_path,
            path_to_config=self.cron.alarm_config_path)
        self.cron.add_cron_entry(entry)
        self.set_alarm_status_message(entry_time)

    def clear_alarm(self):
        """Callback for the "Clear alarm" button: remove the cron entry and
        write a message in the status Label to notify user.
        """
        self.cron.delete_cron_entry()
        self.alarm_status_container.set("Alarm cleared")
        self.alarm_indicator.grid_remove()

        self.root_alarm_time_container.set("")

    def set_alarm_status_message(self, time):
        """Helper function for setting the alarm image and message to the
        alarm window.
        """
        # elements in the alarm setup window:
        self.alarm_indicator.grid(row=2, column=2)
        msg = "Alarm set for {}".format(time)
        self.alarm_status_container.set(msg)

        # also set the time to the main window, below current time display
        self.root_alarm_time_container.set(time)

    def format_window(self, widget, dimensions, title, bg="#D9D9D9"):
        """Given a Tk or Toplevel element set a width and height and assign it to the
        center of the screen.
        Args:
            widget (tk.Tk): the tkinter widget to format
            dimensions (tuple): dimensions of the window as (width, height) pair
            title (str): window title
            bg (str): background color
        """
        widget.configure(background=bg)
        widget.title(title)

        width, height = dimensions
        w_width = widget.winfo_screenwidth()  # width of the screen
        w_height = widget.winfo_screenheight()  # height of the screen

        # compute offsets from the edges of the screen
        dx = (w_width/2) - (width/2)
        dy = (w_height/2) - (height/2)

        widget.geometry("{}x{}+{}+{}".format(width, height, int(dx), int(dy)))


class CronWriter:
    """Helper class for writes cron entries. Uses crontab via subprocess."""

    def __init__(self):
        # format an absolute path to sound_the_alarm.py
        self.alarm_path = os.path.abspath("sound_the_alarm.py")
        self.alarm_config_path = os.path.abspath("alarm.config")  # TODO parametrize?

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
