#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import argparse
import importlib
import os.path

import pydub
import pydub.playback
import alarmenv

# Loop throught the configuration file for enabled components and
# intantiate corresponding classes for processing the sections.

# 1 create an alarmenv and parse configs
# 2 create necessary handlers

# Create mapping between a handler module name and class names for those handlers
handler_map = {
    "get_gcp_tts": "GoogleCloudTTS",
    "get_google_translate_tts": "GoogleTranslateTTSManager",
    "get_festival_tts": "FestivalTTSManager",
    "get_greeting": "Greeting",
    "get_bbc_news": "NewsParser",
    "get_yahoo_weather": "YahooWeatherClient"
}


def main(alarm_env):
    """Read the configuration file, create and play the corresponding alarm."""

    # Check status for internet connection. If no connection detected,
    # play a beeping sound instead of making API calls.
    if not alarm_env.netup:
        play_beep()

    else:
        tts_enabled = alarm_env.config_has_match("main", "readaloud", "1")
        if tts_enabled:
            content = generate_content(alarm_env)
            tts_client = get_tts_client(alarm_env)
            text = "\n".join(content)
            tts_client.play(text)

        # play a beeping sound if readaloud is not enabled
        else:
            play_beep()

        # open a radio stream if enabled
        radio_enabled = alarm_env.config_has_match("radio", "enabled", "1")
        if radio_enabled:
            play_radio(alarm_env)


def generate_content(alarm_env):
    """Loop through the configuration file and process each enabled item."""
    sections = alarm_env.get_enabled_content_sections()

    # for each section get the handler module and create the approriate
    # instance
    contents = []
    for section_name in sections:
        class_ = get_content_parser_class(alarm_env, section_name)

        # create an instance using the config section
        section = alarm_env.get_section(section_name)
        parser = class_(section)

        # call build to run the parser and store output
        parser.build()
        contents.append(parser.get())

    # add ending phrase from the config file
    contents.append(alarm_env.get_value("main", "end"))

    for section in contents:
        print(section)

    return contents


def get_tts_client(alarm_env):
    """Determine which TTS engine to use based on the enabled tts sections
    in the config file. First enabled section is used.
    """
    tts = [s for s in alarm_env.get_sections(exclude_main=True) if
           alarm_env.config_has_match(s, "type", "tts") and
           alarm_env.config_has_match(s, "enabled", "1")
           ]

    # Instantiate the correct class
    if tts:
        tts_section = tts[0]
        class_ = get_content_parser_class(alarm_env, tts_section)
        # read the path to the keyfile if provided/applicable
        key_file = alarm_env.get_value_with_fallback(tts_section, "private_key_file", None)
        client = class_(keyfile=key_file)

    # by default, use the festival tts client
    else:
        from handlers import get_festival_tts
        client = get_festival_tts.FestivalTTSManager()

    return client


def get_content_parser_class(alarm_env, section_name):
    """Given config file section name, create a handler instance, ie. an
    instance of the class matching the listed handler module.
    """
    # use importlib to dynamically import the correct module within
    # the 'handlers' package.
    handler_module_name = alarm_env.get_value(section_name, "handler")[:-3]
    path_to_module = "handlers.{}".format(handler_module_name)
    handler_module = importlib.import_module(path_to_module)

    # get matching class name and use getattr to create the matching instance
    class_name = handler_map[handler_module_name]
    class_ = getattr(handler_module, class_name)

    return class_


def play_beep():
    """Play a beeping sound effect."""
    # Create a path to the mp3 file. If this script was called via cron, we need
    # an absolute path. Since cron runs this script with absolute paths as
    # /path/to/python /path/to/sound_the_alarm.py /path/to/alarm.config
    # use the sys.argv to format an absolute path to the sound file.
    # This is a bit of a hack, there's probably a better way...
    import sys

    path = os.path.abspath("resources/Cool-alarm-tone-notification-sound.mp3")
    if len(sys.argv) > 1:
        base = os.path.dirname(sys.argv[0])
        path = os.path.join(base, "resources", "Cool-alarm-tone-notification-sound.mp3")

    beep = pydub.AudioSegment.from_mp3(path)
    pydub.playback.play(beep)


def play_radio(alarm_env):
    """Play the radio stream defined in the configuration using mplayer."""
    url = alarm_env.get_value("radio", "url")
    cmd = "/usr/bin/mplayer -nolirc -playlist {}".format(url).split()
    try:
        timeout = int(alarm_env.get_value("radio", "timeout"))
    except ValueError:  # raised if empty timeouty in the configuration file
        timeout = None

    subprocess.run(cmd, timeout=timeout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Play the alarm using a specified configuration file")
    parser.add_argument("config", metavar="config", nargs="?",
                        default="alarm.config", help="path to the config file")
    parser.add_argument("--init-config", action="store_true",
                        help="re-create the default configuration file alarm.config. Overwrites existing file.")
    args = parser.parse_args()

    alarm_env = alarmenv.AlarmEnv(args.config)
    alarm_env.validate_config()

    if args.init_config:
        alarm_env.write_default_configuration()

    else:
        main(alarm_env)
