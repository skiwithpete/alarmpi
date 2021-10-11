#!/usr/bin/python3

"""A PyQt5 clock radio application."""

import datetime
import subprocess
import logging
import json
import signal
from functools import partial

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from src import (
    apconfig,
    utils,
    alarm_builder,
    GUIWidgets,
    rpi_utils
)


event_logger = logging.getLogger("eventLogger")


class Clock:
    """Wrapper class for the clock itself. Defines interactions between
    UI elements and backend logic.
    """

    def __init__(self, config_file, **kwargs):
        """Setup GUI windows and various configuration objects.
        params
            config_file (str): name (not path!) of the configuration file in /configs to use.
            kwargs: additional command line parameters passed via main.py
        """
        self.main_window = GUIWidgets.AlarmWindow()
        self.settings_window = GUIWidgets.SettingsWindow()

        # Read the alarm configuration file and initialize and alarmenv object
        self.config = apconfig.AlarmConfig(config_file)

        self.alarm_player = alarm_builder.AlarmBuilder(self.config)
        self.radio = RadioStreamer(self.config["radio"])

        # Setup a QThread and QTimers for building and playing the alarm
        self.alarm_play_thread = AlarmWorker(self.alarm_player, task="play")
        self.alarm_play_thread.play_finished_signal.connect(self.finish_playing_alarm)

        self.alarm_timer = QTimer(self.main_window)
        self.alarm_timer.setSingleShot(True)
        self.alarm_timer.timeout.connect(self.play_alarm)

        self.alarm_build_thread = AlarmWorker(self.alarm_player, task="build")
        self.alarm_build_thread.build_finished_signal.connect(self.finish_building_alarm)

        self.alarm_build_timer = QTimer(self.main_window)
        self.alarm_build_timer.setSingleShot(True)
        self.alarm_build_timer.timeout.connect(self.build_alarm)

        # ... one more worker thread for building and playing an alarm from end to end
        self.build_and_play_thread = AlarmWorker(self.alarm_player, task="build_and_play")
        self.build_and_play_thread.build_finished_signal.connect(self.finish_building_alarm)
        self.build_and_play_thread.play_finished_signal.connect(self.finish_playing_alarm)

        # Set debug signal handlers for custom debug signal and keyboard event
        signal.signal(signal.SIGUSR1, self._debug_signal_handler)
        self.main_window.keyPressEvent = self._debug_key_press_event

        if kwargs.get("fullscreen"):
            self.main_window.showFullScreen()

            # Hide mouse cursor unless in debug mode
            if not kwargs.get("debug"):
                self.main_window.setCursor(Qt.BlankCursor)
                self.settings_window.setCursor(Qt.BlankCursor)

        if kwargs.get("debug"):
            self.config["radio"]["enabled"] = False

            # Set special debug flags
            self.config["debug"] = {
                "DO_NOT_PLAY_ALARM": True
            }

            # Force enable brightness buttons
            self.config.rpi_brightness_write_access = True

    def setup(self):
        """Setup various button handlers as well as weather and train data polling
        for the main windows side bar.
        """
        self.setup_button_handlers()

        # Enable various plugin pollers if enabled in the config.
        # Note: plugins defined as instance variables to prevent
        # their pollers from being garbage collected.
        if self.config["plugins"]["openweathermap.org"]["enabled"]:
            from src.plugins import weather
            self.weather_plugin = weather.WeatherPlugin(self)
            self.weather_plugin.create_widgets()
            self.weather_plugin.setup_polling()

        if self.config["plugins"]["HSL"]["enabled"]:
            from src.plugins import trains
            self.train_plugin = trains.TrainPlugin(self)
            self.train_plugin.create_widgets()
            self.train_plugin.setup_polling()

        if self.config["plugins"]["DHT22"]["enabled"]:
            from src.plugins import dht22
            self.dht22_plugin = dht22.DHT22Plugin(self)
            self.dht22_plugin.create_widgets()
            self.dht22_plugin.setup_polling()

        # Set a higher row streches to the last used row to push elements
        # closer together
        nrows = self.main_window.right_plugin_grid.rowCount()
        self.main_window.right_plugin_grid.setRowStretch(nrows-1, 1)

        # Setup settings window's checkbox initial values:
        tts_enabled = self.config["main"]["TTS"]
        self.settings_window.readaloud_checkbox.setChecked(tts_enabled)

        nightmode = self.config["main"]["nighttime"].get("enabled", False)
        self.settings_window.nightmode_checkbox.setChecked(nightmode)

        alarm_brightness_enabled = self.config["main"]["full_brightness_on_alarm"]
        self.settings_window.alarm_brightness_checkbox.setChecked(alarm_brightness_enabled)

        # Set main window's alarm time display to currently active alarm time
        alarm_time = self.get_current_active_alarm()
        if alarm_time:
            self.main_window.alarm_time_lcd.display(alarm_time)

        self.screen_blank_timer = QTimer(self.main_window)
        self.screen_blank_timer.setSingleShot(True)
        self.screen_blank_timer.timeout.connect(self.blank_screen_and_hide_control_buttons)

        self.main_window.mouseReleaseEvent = self.on_release_event_handler

        # Set radio stations from config to the settings window options
        self.radio_streams = self.config["radio"]["urls"]
        self.settings_window.radio_station_combo_box.addItems(self.radio_streams.keys())

        # Ensure station set as default is set as current item
        default_station = self.config["radio"]["default"]
        self.settings_window.radio_station_combo_box.setCurrentText(default_station)

    def setup_button_handlers(self):
        """Setup button handlers for the main window and settings window."""
        # Setup references to main control buttons in both windows
        self.settings_button = self.main_window.control_buttons["Settings"]
        self.radio_button = self.main_window.control_buttons["Radio"]
        self.blank_button = self.main_window.control_buttons["Blank"]
        self.close_button = self.main_window.control_buttons["Close"]

        self.alarm_play_button = self.settings_window.control_buttons["Play Now"]
        window_button = self.settings_window.control_buttons["Toggle\nWindow"]
        brightness_button = self.settings_window.control_buttons["Toggle\nBrightness"]

        alarm_set_button = self.settings_window.numpad_buttons["set"]
        alarm_clear_button = self.settings_window.numpad_buttons["clear"]

        # Disable backlight manipulation buttons if the underlying system
        # files dont't exists (ie. not a Raspberry Pi) or no write access to them.
        if not self.config.rpi_brightness_write_access:
            msg = [
                "No write access to system backlight brightness files:",
                "\t" + rpi_utils.BRIGHTNESS_FILE,
                "\t" + rpi_utils.POWER_FILE,
                "Disabling brightness buttons"
            ]
            event_logger.info("\n".join(msg))
            self.blank_button.setEnabled(False)
            brightness_button.setEnabled(False)

        # Set button handlers for buttons requiring interactions between helper classes
        # ** main window buttons **
        self.settings_button.clicked.connect(self.open_settings_window)

        # Set the radio button as an on/off toggle
        self.radio_button.setCheckable(True)
        radio_play_slot = partial(self.play_radio, url=None)
        self.radio_button.clicked.connect(radio_play_slot)

        self.blank_button.clicked.connect(self.blank_screen_and_hide_control_buttons)
        self.close_button.clicked.connect(self.cleanup_and_exit)

        # ** settings window buttons **
        # Set brightness toggle button with a low brightness value read from the config file
        low_brightness = self.config["main"].get("low_brightness", 12)
        brightness_toggle_slot = partial(rpi_utils.toggle_display_backlight_brightness, low_brightness=low_brightness)
        brightness_button.clicked.connect(brightness_toggle_slot)

        self.alarm_play_button.clicked.connect(self.build_and_play_alarm)
        window_button.clicked.connect(self.toggle_display_mode)

        alarm_set_button.clicked.connect(self.set_alarm)
        alarm_clear_button.clicked.connect(self.clear_alarm)

        # Settings window checkbox callbacks
        self.settings_window.readaloud_checkbox.stateChanged.connect(
            lambda state: self.config.config["main"].update({"TTS": state == Qt.CheckState.Checked})
        )
        self.settings_window.nightmode_checkbox.stateChanged.connect(
            lambda state: self.config.config["main"]["nighttime"].update({"enabled": state == Qt.CheckState.Checked})
        )
        self.settings_window.alarm_brightness_checkbox.stateChanged.connect(
            lambda state: self.config.config["main"].update({"full_brightness_on_alarm": state == Qt.CheckState.Checked})
        )

        self.settings_window.volume_slider.valueChanged.connect(self.set_volume)
        # Set initial handle position and icon. Disable the slider if
        # couldn't get a meaningful volume level (ie. invalid card in configuration)
        try:
            volume_level = utils.get_volume(self.config["alsa"]["card"])
            self.set_volume(volume_level)
            self.settings_window.volume_slider.setValue(volume_level)
        except AttributeError as e:
            self.settings_window.volume_slider.setEnabled(False)
            self.set_volume(0) # Sets icon to muted (as well as attempting to set PCM control to selected card)
            event_logger.warning("Couldn't get volume level. Wrong card value in configuration? Disabling volume slider.")

    def open_settings_window(self):
        """Button callback - settings window. Open the settings window and
        clear any existing screen blanking timer.
        and dislpay the window.
        """
        self.screen_blank_timer.stop()
        self.settings_window.show()
        # Ensure the window is raised in top, useful when main window is fullscreened
        # and settings window is accidentally sent to the background
        getattr(self.settings_window, "raise")()
        self.settings_window.activateWindow()
        event_logger.debug("Settings window opened")

    def on_release_event_handler(self, event):
        """Event handler for touching the screen. Ensure screen is turned on.
        If and alarm is set, nightmode is enabled and it is currently nighttime,
        sets a short timer for blanking the screen.
        """
        # Get screen state before the event occured and set it as enabled.
        event_logger.debug("Activating display")
        old_screen_state = rpi_utils.get_and_set_screen_state("on")
        self.show_control_buttons()

        alarm_time = self.get_current_active_alarm()
        if alarm_time is None:
            return

        # Set screen blanking timeout if the screen was blank before the event
        # and it is currently nightime.
        if self._nightmode_active() and old_screen_state == "off":
            self.screen_blank_timer.start(3*1000)  # 3 second timer
            event_logger.info("Screen blank timer activated")

    def set_alarm(self):
        """Button callback - set alarm. Sets timers for alarm build and alarm play based
        on a valid value on settings window's alarm time widget. Updates main window's
        alarm label.
        On invalid time value sets an error message to error label.
        """
        time_str = self.settings_window.validate_alarm_input()
        if time_str:
            # Update displayed alarm time settings and main window
            self.main_window.alarm_time_lcd.display(time_str)
            self.settings_window.set_alarm_input_success_message_with_time(time_str)
            self.config["main"]["alarm_time"] = time_str

            # Set alarm play timer
            self.alarm_dt = utils.time_str_to_dt(time_str)
            now = datetime.datetime.now()
            alarm_wait_ms = (self.alarm_dt - now).seconds * 1000

            event_logger.info("Setting alarm for %s", time_str)
            self.alarm_timer.start(alarm_wait_ms)

            # Setup alarm build time for 5 minutes earlier (given large enough timer)
            ALARM_BUILD_DELTA = 5 * 60 * 1000
            alarm_build_wait_ms = max((0, alarm_wait_ms - ALARM_BUILD_DELTA))  # 0 if not enough time

            alarm_build_dt = self.alarm_dt - datetime.timedelta(minutes=5)
            event_logger.info("Setting alarm build for %s", alarm_build_dt.strftime("%H:%M"))
            self.alarm_build_timer.start(alarm_build_wait_ms)

            # Set screen brightness to low if nighttime and nigthmode enabled
            if self._nightmode_active():
                low_brightness = self.config["main"].get("low_brightness", 12)
                rpi_utils.set_display_backlight_brightness(low_brightness)

    def clear_alarm(self):
        """Button callback - clear alarm. Stop any running alarm timers and clears all
        alarm related labels.
        """
        self.alarm_timer.stop()
        self.alarm_build_timer.stop()
        event_logger.info("Alarm cleared")
        self.settings_window.clear_alarm()
        self.main_window.alarm_time_lcd.display("")
        self.config["main"]["alarm_time"] = ""

    def get_current_active_alarm(self):
        """Check for existing running alarm timers and return alarm time in HH:MM format."""
        active = self.alarm_timer.isActive()
        if active:
            return self.alarm_dt.strftime("%H:%M")

    def play_radio(self, url=None):
        """Button callback - play radio. Open or close the radio stream
        depending on the button's current state.
        Args:
            url (string): the url of the stream to play. If none, currently active
                stream from the settings window QComboBox is used.
        """
        button = self.main_window.control_buttons["Radio"]

        # If no stream url was passed, use currently active station from settings window
        # QComboBox
        if url is None:
            current_radio_station = self.settings_window.radio_station_combo_box.currentText()
            url = self.radio_streams[current_radio_station]

        else:
            # Look for station name from listed streams in stream config file
            current_radio_station = ""

            for name, stream_url in self.radio_streams.items():
                if stream_url == url:
                    current_radio_station = name
                    break

        # The radio button is a checkable (ie. a toggle): radio should start playing
        # when the button gets checked and stop when state changes to not checked.
        # (The state change occurs before this callback runs.)
        if button.isChecked():
            self.main_window._show_radio_play_indicator(current_radio_station)
            self.radio.play(url)
        else:
            self.main_window._hide_radio_play_indicator()
            self.radio.stop()

    def play_alarm(self):
        """Alarm timer callback: Play a previously built alarm.
        Clears alarm related labels from both windows.
        """
        # Update main display
        self.main_window.alarm_time_lcd.display("")
        self.enable_screen_and_show_control_buttons()
        rpi_utils.set_display_backlight_brightness(rpi_utils.HIGH_BRIGHTNESS)

        # Clear 'Alarm set for ...' label in the settings window
        self.settings_window.alarm_time_status_label.setText("")

        self.alarm_play_thread.start()

    def finish_playing_alarm(self):
        """Slot for finishing alarm play: re-enable the play button
        and, if enabled, starts a separated cvlc process for the radio stream.
        """
        self.alarm_play_button.setEnabled(True)
        
        if self.config["radio"]["enabled"]:
            # Toggle the radio button and pass the default stream
            # the radio player.
            self.main_window.control_buttons["Radio"].toggle()
            default_station = self.config["radio"]["default"]
            url = self.radio_streams[default_station]
            self.play_radio(url=url)

    def build_alarm(self):
        """Alarm build timer callback: start building an alarm and display
        loader icon.
        """
        self.main_window.waiting_spinner.start()
        self.alarm_build_thread.start()

    def finish_building_alarm(self):
        """Slot for finishing alarm build: stop the loading icon."""
        self.main_window.waiting_spinner.stop()

    def build_and_play_alarm(self):
        """Button callback - play alarm. Generate and play an alarm."""
        # Stop any playing radio stream
        if self.radio_button.isChecked():
            self.radio_button.click()

        self.alarm_play_button.setEnabled(False)
        self.main_window.waiting_spinner.start()
        self.build_and_play_thread.start()

    def toggle_display_mode(self):
        """Button callback - toggle window. Change main window display mode between
        fullscreen and windowed depending on current its state.
        """
        if self.main_window.windowState() == Qt.WindowFullScreen:
            self.main_window.showNormal()
        else:
            self.main_window.showFullScreen()
            # Keep the settings window active to prevent main window from
            # burying it
            self.settings_window.activateWindow()

    def blank_screen_and_hide_control_buttons(self):
        """Button callback - blank screen. Turn off display backlight power and
        hide the main window's control buttons to prevent accidentally hitting
        them when the screen in blank.
        """
        event_logger.debug("Blanking display")
        rpi_utils.toggle_screen_state("off")
        self.hide_control_buttons()

    def enable_screen_and_show_control_buttons(self):
        """Turn on display backlight power and show the main window's control buttons."""
        event_logger.debug("Activating display")
        rpi_utils.toggle_screen_state("on")
        self.show_control_buttons()

    def hide_control_buttons(self):
        """Hide main window's bottom row buttons."""
        self.settings_button.hide()
        self.radio_button.hide()
        self.blank_button.hide()
        self.close_button.hide()

    def show_control_buttons(self):
        """Display main window's bottom row buttons."""
        self.settings_button.show()
        self.radio_button.show()
        self.blank_button.show()
        self.close_button.show()

    def set_volume(self, value):
        """Slider callback - set system volume level to match volume slider lever and
        update volume level icon.
        """
        utils.set_volume(self.config["alsa"]["card"], value) # Sets the actual volume level

        if value == 0:
            mode = "muted"
        elif value <= 25:
            mode = "low"
        elif value <= 75:
            mode = "medium"
        else:
            mode = "high"
        
        icon = utils.get_volume_icon(mode)
        self.settings_window.volume_label.setPixmap(icon)

    def cleanup_and_exit(self):
        """Button callback - Exit application. Close any existing radio streams and the
        application itself.
        """
        self.radio.stop()

        # Ensure display is on and at full brightness
        rpi_utils.toggle_screen_state("on")
        rpi_utils.set_display_backlight_brightness(rpi_utils.HIGH_BRIGHTNESS)
        QApplication.instance().quit()

    def _nightmode_active(self):
        """Helper function for checking if nightmode is enabled and it is currently nighttime."""
        nightmode = self.config["main"]["nighttime"].get("enabled")
        is_nighttime = utils.time_is_in(
            self.config["main"]["nighttime"]["start"],
            self.config["main"]["nighttime"]["end"]
        )
        return nightmode and is_nighttime

    def _debug_signal_handler(self, sig, frame):
        """Dump current state to file."""
        OUTPUT_FILE = "debug_info.txt"
        with open(OUTPUT_FILE, "w") as f:
            f.write("config file: {}\n".format(self.config.path_to_config))
            json.dump(self.config.config, f, indent=4)

            f.write("\n{:60} {:9} {:12} {:14}".format("window", "isVisible", "isFullScreen", "isActiveWindow"))
            for window in (self.main_window, self.settings_window):
                f.write("\n{:60} {:9} {:12} {:14}".format(
                    str(window),
                    window.isVisible(),
                    window.isFullScreen(),
                    window.isActiveWindow()
                ))

        event_logger.info("Debug status written to %s", OUTPUT_FILE)      

    def _debug_key_press_event(self, event):
        """Keyboard event handler, run the debug signal handler when F2 is pressed."""
        if event.key() == Qt.Key_F2:
            self._debug_signal_handler(None, None)

class AlarmWorker(QThread):
    play_finished_signal = pyqtSignal(int)
    build_finished_signal = pyqtSignal(int)
    audio = None

    def __init__(self, builder, *args, task):
        super().__init__()
        self.alarm_builder = builder
        self.task = task

    def _build(self):
        """Build and alarm."""
        event_logger.info("Building alarm")
        AlarmWorker.audio = self.alarm_builder.build()

    def _play(self):
        """Play an existing alarm."""
        # Play unless explicitely ignored in config
        if not self.alarm_builder.config._get_debug_option("DO_NOT_PLAY_ALARM"):
            self.alarm_builder.play(AlarmWorker.audio)      

    def run(self):
        if self.task == "build":
            self._build()
            self.build_finished_signal.emit(1)
        elif self.task == "play":
            self._play()
            self.play_finished_signal.emit(1)
        elif self.task == "build_and_play":
            self._build()
            self.build_finished_signal.emit(1)
            self._play()
            self.play_finished_signal.emit(1)

class RadioStreamer:
    """Helper class for playing a radio stream via cvlc."""
    def __init__(self, config):
        self.process = None
        self.config = config

    def is_playing(self):
        """Check if cvlc is currently running."""
        return self.process is not None

    def play(self, url):
        """Open a radio stream as a child process. The stream will continue to run
        in the background.
        """
        args = self.config.get("args", "")
        cmd = "/usr/bin/cvlc {} {}".format(url, args)
        event_logger.info("Running %s", cmd)

        # Run the command via Popen directly to open the stream as an independent child
        # process. This way we do not wait for the stream to finish.
        # Output is captured (truncated) to file.
        with open("logs/radio.log", "w") as f:
            self.process = subprocess.Popen(cmd.split(), stdout=f, stderr=subprocess.STDOUT)

    def stop(self):
        """Terminate the running cvlc process."""
        try:
            self.process.terminate()
            self.process = None
        except AttributeError:
            return
