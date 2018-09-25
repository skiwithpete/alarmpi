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
        self.root = tk.Tk()
        self.root.title("Clock")
        self.root.geometry("600x320")
        for x in range(2):
            tk.Grid.columnconfigure(self.root, x, weight=1)

        for y in range(3):
            tk.Grid.rowconfigure(self.root, y, weight=1)

        # self.root.resizable(0, 0) #Don't allow resizing in the x or y direction

        # Define a Label for displaying the time
        self.clock = tk.Label(self.root, font=('times', 36, 'bold'), bg='#090201', fg='#840303')
        self.clock.grid(row=0, column=0, ipadx=50, columnspan=2, rowspan=2,
                        sticky=tk.E+tk.W+tk.S+tk.N)

        # Attach buttons for setting the alarm and exiting
        self.alarm_button = tk.Button(self.root, text="Set alarm", command=self.show_alarm_window)
        self.alarm_button.grid(row=2, column=0, sticky=tk.E+tk.W+tk.S+tk.N)

        self.exit_button = tk.Button(self.root, text="Close", command=self.root.destroy)
        self.exit_button.grid(row=2, column=1, sticky=tk.E+tk.W+tk.S+tk.N)

        self.cron = CronWriter()
        self.tick()

    def tick(self):
        """Update the current time value every 1 second."""
        s = time.strftime('%H:%M:%S')
        if s != self.clock["text"]:
            self.clock["text"] = s
        self.clock.after(1000, self.tick)

    def show_alarm_window(self):
        """Create a new window for setting the alarm time."""
        settings_root = tk.Toplevel()
        settings_root.title("Set Alarm")

        # set window dimensions and place to the center of screen
        w = 500
        h = 160

        ws = settings_root.winfo_screenwidth()  # width of the screen
        hs = settings_root.winfo_screenheight()  # height of the screen

        # calculate x and y coordinates for the Toplevel
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        settings_root.geometry("{}x{}+{}+{}".format(w, h, int(x), int(y)))

        for x in range(11):
            tk.Grid.columnconfigure(settings_root, x, weight=1)

        for y in range(3):
            tk.Grid.rowconfigure(settings_root, y, weight=1)

        # wide Label for info text
        info_label = tk.Label(settings_root, text="Use the toggles to set alarm time")
        info_label.grid(row=0, columnspan=10)

        # Right panel for displaying the alarm time
        self.display_time_container = tk.StringVar()
        self.display_time_container.set("00:00")
        display_label = tk.Label(settings_root, textvariable=self.display_time_container)
        display_label.grid(row=1, column=10, columnspan=4)

        # Add Label for "alarm set/cleared" message beneath the time display
        self.alarm_status_info_container = tk.StringVar()
        alarm_status_label = tk.Label(settings_root, textvariable=self.alarm_status_info_container)
        alarm_status_label.grid(row=2, column=10, columnspan=4)

        # Show a bell icon if an alarm is currently active
        image = Image.open("resources/alarm-1673577_640.png")
        image = image.resize((28, 28), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)

        self.alarm_indicator = tk.Label(settings_root, image=photo)
        self.alarm_indicator.image = photo  # keep a reference to prevent garbage collection

        if self.cron.active_alarm():
            self.alarm_indicator.grid(row=0, column=10)

        # Make Labels for hour and minute titles
        hour_label = tk.Label(settings_root, text="H: ")
        hour_label.grid(row=1, column=1)
        minute_label = tk.Label(settings_root, text="M: ")
        minute_label.grid(row=2, column=1)

        # make Buttons for toggling each bit in hour and minute
        hour_indicators = []  # store IntVars for each CheckButton
        for i in range(5):
            var = tk.IntVar()
            hour_indicators.append(var)
            hour_button = tk.Checkbutton(settings_root, text=str(2**i), variable=var,
                                         indicatoron=False, command=lambda: self.set_alarm_display_time(hour_indicators))
            hour_button.grid(row=1, column=i+2, sticky=tk.W+tk.E+tk.S+tk.N, ipadx=5, ipady=5)

        minute_indicators = []
        for i in range(6):
            var = tk.IntVar()
            minute_indicators.append(var)
            minute_button = tk.Checkbutton(settings_root, text=str(2**i), variable=var,
                                           indicatoron=False, command=lambda: self.set_alarm_display_time(minute_indicators))
            minute_button.grid(row=2, column=i+2, sticky=tk.W+tk.E+tk.S+tk.N, ipadx=5, ipady=5)

        # Add buttons for clearing and confirming the alarm and closing the window
        set_alarm_button = tk.Button(settings_root, text="Set alarm",
                                     command=self.set_alarm)
        set_alarm_button.grid(row=3, column=1, columnspan=2, sticky=tk.E+tk.W)

        clear_alarm_button = tk.Button(settings_root, text="Clear alarm", command=self.clear_alarm)
        clear_alarm_button.grid(row=3, column=3, columnspan=2, sticky=tk.E+tk.W)

        close_button = tk.Button(settings_root, text="Close", command=settings_root.destroy)
        close_button.grid(row=3, column=5, columnspan=2, sticky=tk.E+tk.W)

    def set_alarm_display_time(self, indicators):
        """Update the Label container value for selected alarm time."""
        # transform the list of bits to integer value
        summed_value = sum([ind_value.get() * 2**i for i, ind_value in enumerate(indicators)])
        summed_value = str(summed_value).zfill(2)

        # determine whether the indicators are for minutes or hours from the list length
        old_value = self.display_time_container.get()
        if len(indicators) == 5:
            updated_value = summed_value + old_value[2:]
        else:
            updated_value = old_value[:3] + summed_value

        self.display_time_container.set(updated_value)

    def set_alarm(self):
        """Callback for "Set alarm" button: add a new cron entry for alarm and
        display a message for the user.
        """
        try:
            entry_time = self.display_time_container.get()
            t = time.strptime(entry_time, "%H:%M")
        except ValueError:
            self.alarm_status_info_container.set("Invalid time")
            return

        # define a cron entry with absolute paths to the executable and alarm script
        entry = "{min} {hour} * * 1-5 {python_exec} {path_to_alarm} {path_to_config}".format(
            hour=t.tm_hour,
            min=t.tm_min,
            python_exec=sys.executable,
            path_to_alarm=self.cron.alarm_path,
            path_to_config=self.cron.alarm_config_path)
        self.cron.add_cron_entry(entry)
        self.alarm_status_info_container.set("Alarm set for {}".format(entry_time))
        self.alarm_indicator.grid(row=0, column=11)

    def clear_alarm(self):
        """Callback for the "Clear alarm" button: remove the cron entry and
        write a message in the status Label to notify user.
        """
        self.cron.delete_cron_entry()
        self.alarm_status_info_container.set("Alarm cleared")
        self.alarm_indicator.grid_remove()


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

    def active_alarm(self):
        """Check whether there is a valid alarm entry currently in crontab."""
        crontab = subprocess.check_output(["crontab", "-l"]).decode()
        return self.alarm_path in crontab

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
        """Add an entry for sound_the_alarm.py. Existing entries are removed."""
        crontab_lines = self.get_crontab_lines_without_alarm()

        # Add new entry and overwrite the crontab file
        # crontab_lines.append("\n")
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
