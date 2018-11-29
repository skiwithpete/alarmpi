#!/usr/bin/env python

"""
A Tkinter app displaying the current time and for setting up an alarm via a
cron entry.
"""

import datetime
import time
import sys
import os
import subprocess
import signal
import tkinter as tk
from PIL import Image, ImageTk

import sound_the_alarm


class Clock:
    """A Tkinter GUI for displaying the current time and setting the alarm."""

    def __init__(self, config_file, **kwargs):
        """Create the root window for displaying time."""
        self.root = tk.Tk()
        self.cron = CronWriter(config_file)
        self.alarm = sound_the_alarm.Alarm(config_file)
        self.radio = RadioStreamer()
        self.kwargs = kwargs

        # determine whether the host system is a Raspberry Pi by checking
        # the existance of a system brightness file.
        self.is_rpi = os.path.isfile("/sys/class/backlight/rpi_backlight/brightness")

        # store current alarm time from cron as an attribute in HH:MM
        self.current_alarm_time = self.cron.get_current_alarm()

        # init StringVars for various widgets needed in multiple methods
        # 1 main window:
        self.clock_time_var = tk.StringVar()  # current time
        self.clock_alarm_indicator_var = tk.StringVar()  # alarm time

        # 2 alarm setup window
        self.alarm_time_var = tk.StringVar()  # selected alarm time
        self.alarm_time_var.set("00:00")
        self.alarm_status_var = tk.StringVar()  # status messages ('alarm set', 'invalid value', etc.)

        # Current active alarm display should be cleared if no active alarm
        # for the next day and re-set if alarm is active the next day
        # (ie. don't show alarm as active during weekends)
        # Add bindings for clearing and setting the active alarm label.
        self.root.bind("<Button-1>", self.update_on_touch_tasks)
        signal.signal(signal.SIGUSR1, self.signal_handler)

    def tick(self):
        """Update the current time value in the main clock label every 1 second."""
        s = time.strftime("%H:%M:%S")
        self.clock_time_var.set(s)
        self.root.after(1000, self.tick)

    def run(self):
        """Validate configuration file path, create the main window run mainloop.
        """
        self.cron.validate_config_path()
        self.create_main_window()
        self.root.mainloop()

    def destroy(self):
        """Destroy the main window and kill any running radio streams."""
        self.radio.stop()
        self.root.destroy()

    def signal_handler(self, sig, frame):
        """Signal handler for incoming radio stream requests. Used to receive SIGUSR1
        signals from sound_the_alarm denoting a request to open a radio stream and to
        set the radio button as pressed. Also runs a check to see whether the displayed
        alarm time in the main window should be hidden (ie. no alarm the next day)."""
        self.play_radio()
        self.set_active_alarm_indicator()

    def create_main_window(self):
        """Create the main window. Contains labels for current and alarm time as well as
        buttons for accessing the alarm setup window.
        """
        # rows: 3, columns: 5
        RED = "#FF1414"
        BLACK = "#090201"

        self.format_window(self.root, dimensions=(600, 320), title="Clock", bg=BLACK)

        # set main window to fullscreen if command line flag for it was provided
        # (overrides the dimentions above)
        if self.kwargs.get("fullscreen"):
            self.root.attributes("-fullscreen", True)
            self.root.config(cursor="none")  # hide mouse cursor

        # set row and column weights so widgets expand to all available space
        for i in range(5):
            tk.Grid.columnconfigure(self.root, i, weight=1)

        for i in range(3):
            tk.Grid.rowconfigure(self.root, i, weight=1)

        # Row 0: label for displaying current time
        clock_label = tk.Label(
            self.root,
            font=("times", 48, "bold"),
            textvariable=self.clock_time_var,
            fg=RED,
            bg=BLACK
        )
        clock_label.grid(row=0, column=1, ipadx=50, columnspan=3, rowspan=1,
                         sticky="sew")

        # Row 1: label for showing set alarm time (if any)
        alarm_time_label = tk.Label(
            self.root,
            font=("times", 22, "bold"),
            textvariable=self.clock_alarm_indicator_var,
            fg=RED,
            bg=BLACK
        )
        alarm_time_label.grid(row=1, column=1, columnspan=3, sticky="new")

        # only display the alarm time during weekdays
        self.set_active_alarm_indicator()

        # Row 2: control buttons
        tk.Button(self.root, text="Set alarm",
                  command=self.create_alarm_window).grid(row=2, column=0, sticky="nsew")

        # 'Play radio' button. a tkinter Button whose relief is controlled by the
        # callback so as to keep it as pressed until the stream is stopped
        self.radio_button = tk.Button(
            self.root,
            text="Play radio",
            command=self.play_radio
        )
        self.radio_button.grid(row=2, column=1, sticky="nsew")

        # disable the button if no url provided in the config file
        if not self.alarm.env.radio_url:
            self.radio_button.config(state=tk.DISABLED)

        brightness_button = tk.Button(
            self.root,
            text="Toggle brightness",
            command=Clock.set_screen_brightness
        )
        brightness_button.grid(row=2, column=2, sticky="nsew")

        sleep_button = tk.Button(
            self.root,
            text="Sleep",
            command=Clock.put_screen_to_sleep
        )
        sleep_button.grid(row=2, column=3, sticky="nsew")

        # disable brigtness and sleep button if the host system is not a Raspberry Pi
        if not self.is_rpi:
            brightness_button.config(state=tk.DISABLED)
            sleep_button.config(state=tk.DISABLED)

        tk.Button(self.root, text="Close",
                  command=self.destroy).grid(row=2, column=4, sticky="nsew")

        self.tick()

    def create_alarm_window(self):
        """Create a new window for scheduling the alarm. Contains toggle buttons
        for setting the minute and hour value, labels for displaying the selection
        and buttons for confirming.
        """
        # rows: 4 columns: 7

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

        # reset the selected alarm label every time the setup window is opened
        self.alarm_time_var.set("00:00")
        tk.Label(top, textvariable=self.alarm_time_var).grid(row=1, column=3)

        # label for displaying status messages upon setting the alarm
        tk.Label(top, textvariable=self.alarm_status_var).grid(row=2, column=3)

        image = Image.open("resources/alarm-1673577_640.png")
        image = image.resize((28, 28), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)

        self.alarm_indicator = tk.Label(top, image=photo)
        self.alarm_indicator.image = photo  # keep a reference!

        # check for existing alarm in cron and set indicator to main window
        if self.current_alarm_time:
            self.set_alarm_status_message(self.current_alarm_time)

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
        """Given a type and a value, update the label displaying the currently selected alarm time
        in the alarm setup window. Note: output may be invalid time value such as "16:64". These are
        invalidated in the alarm setup callback.
        Args:
            type_ (string): Either 'hour' or 'minute'. Determines the part of the time to update.
            value (int): The value to add to existing hour or minute part of the alarm time.
        """
        # get the currently displayed value in the setup window as base
        old_alarm_time = self.alarm_time_var.get()

        hour = int(old_alarm_time.split(":")[0])
        minute = int(old_alarm_time.split(":")[1])

        if type_ == "hour":
            new_hour = hour + value
            new_value = str(new_hour).zfill(2) + ":" + str(minute).zfill(2)

        else:
            new_minute = minute + value
            new_value = str(hour).zfill(2) + ":" + str(new_minute).zfill(2)

        self.alarm_time_var.set(new_value)

    def set_alarm(self):
        """Callback for "Set alarm" button: write a new cron entry for the alarm and
        display a message for the user. Existing cron alarms will be overwritten
        Invalid time values are not accepted.
        """
        # TODO: don't hard code the date?
        try:
            entry_time = self.alarm_time_var.get()
            t = time.strptime(entry_time, "%H:%M")
        except ValueError:
            self.alarm_status_var.set("Invalid time")
            return

        # define a cron entry with absolute paths to the executable and alarm script
        entry = "{min} {hour} * * 1-5 {python_exec} {path_to_alarm} {path_to_config}".format(
            hour=t.tm_hour,
            min=t.tm_min,
            python_exec=sys.executable,
            path_to_alarm=self.cron.alarm_path,
            path_to_config=self.cron.config_file)
        self.cron.add_cron_entry(entry)
        self.current_alarm_time = entry_time
        self.set_alarm_status_message(entry_time)

    def clear_alarm(self):
        """Callback for the "Clear alarm" button: remove the cron entry and
        write a message in the status Label to notify user.
        """
        self.cron.delete_cron_entry()
        self.alarm_status_var.set("Alarm cleared")
        self.alarm_indicator.grid_remove()

        self.current_alarm_time = ""
        self.clock_alarm_indicator_var.set("")

    def set_alarm_status_message(self, time):
        """Helper function for setting the alarm image and message to the
        alarm window.
        """
        # elements in the alarm setup window:
        self.alarm_indicator.grid(row=2, column=2)
        msg = "Alarm set for {}".format(time)
        self.alarm_status_var.set(msg)

        # also set the time to the main window, below current time
        self.set_active_alarm_indicator()

    def set_active_alarm_indicator(self):
        """Updates the main window label for displaying set alarm time. No time
        should be displayed during weekends, since the alarm only playes on weekdays.
        """
        # TODO support for dynamic alarm times. Currently this whole script assumes
        # the alarm should only be played on weekdays and set_alarm is hard coded
        # to set the date part to 1-5. Maybe do something else instead?
        alarm_time = self.current_alarm_time  # HH:MM
        if not alarm_time:
            return

        now = datetime.datetime.now()
        if self.weekend(now):
            self.clock_alarm_indicator_var.set("")
        else:
            self.clock_alarm_indicator_var.set(alarm_time)

    def update_on_touch_tasks(self, event):
        """Callback to the main window's event binding.
         Hide/unhide the displayed alarm time if necessary. Ie. alarm time should
         only be showed on weekdays.
        """
        self.set_active_alarm_indicator()

    def weekend(self, d):
        """Helper function. Check whether a datetime d is between friday's alarm
        and sunday 21:00.
        """
        dow = d.weekday()  # 0 == monday
        alarm_time = time.strptime(self.current_alarm_time, "%H:%M")

        # create dummy datetimes for same date as d and time values matching the alarm
        # display boundaries
        min_time = d.replace(hour=alarm_time.tm_hour, minute=alarm_time.tm_min)
        max_time = d.replace(hour=21, minute=0)

        friday = (dow == 4 and d >= min_time)
        saturday = (dow == 5)
        sunday = (dow == 6 and d <= max_time)

        return (friday or saturday or sunday)

    def format_window(self, widget, dimensions, title, bg="#D9D9D9"):
        """Helper function for formatting a window. Given a Tk or Toplevel
        element set a width and height and assign it to the center of the screen.
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

    def play_radio(self):
        """Callback to the 'Play radio' button: open or close the radio stream
        depending on whether it is currently running.
        """
        # change the relief of the button
        if self.radio_button["relief"] == tk.SUNKEN:
            self.radio_button.config(relief=tk.RAISED)
        else:
            self.radio_button.config(relief=tk.SUNKEN)

        if self.radio.is_playing():
            self.radio.stop()
        else:
            self.radio.play(self.alarm.env.radio_url)

    @staticmethod
    def set_screen_brightness():
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
        else:
            new_brightness = LOW

        with open(PATH, "w") as f:
            f.write(str(new_brightness))

    @staticmethod
    def put_screen_to_sleep():
        """Put Raspberry pi touch display to sleep using the command
            XAUTHORITY=/home/pi/.Xauthority DISPLAY=:0.0 xset dpms force off
        The display will wakeup on touch.
        See https://stackoverflow.com/questions/39926012/raspberry-pi-enter-display-sleep

        The display can also be turned off by setting
        /sys/class/backlight/rpi_backlight/bl_power to 1, but this can only be
        recovered by changing the value back to 0 via ssh.
        """
        cmd = "xset dpms force off".split()
        # set required env variables so we don't need to run the whole command
        # with shell=True
        env = {"XAUTHORITY": "/home/pi/.Xauthority", "DISPLAY": ":0.0"}
        subprocess.run(cmd, env=env)


class RadioStreamer:
    """Helper class for playing a radio stream via mplayer."""

    def __init__(self):
        self.active = []  # list for opened streams (ie. Popen instances)

    def is_playing(self):
        """Check if mplayer is currently running. Return True if it is."""
        return self.active != []  # return a boolean for clarity

    def play(self, url):
        """Open a radio stream as a child process. The stream will continue to run
        in the background."""
        cmd = "/usr/bin/mplayer -quiet -nolirc -playlist {} -loop 0".format(url).split()
        # Run the command via Popen directly to open the stream as an independent child
        # process. This way we do not wait for the stream to finish.
        p = subprocess.Popen(cmd)
        self.active.append(p)

    def stop(self):
        """Kill all opened streams."""
        for process in self.active:
            process.kill()
        self.active = []


class CronWriter:
    """Helper class for writes cron entries. Uses crontab via subprocess."""

    def __init__(self, config_file):
        # format absolute paths to sound_the_alarm.py and the config file
        self.alarm_path = os.path.abspath("sound_the_alarm.py")
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

    def validate_config_path(self):
        """Check whether self.config_file exists."""
        if not os.path.isfile(self.config_file):
            raise RuntimeError("No such file: {}".format(self.config_file))
