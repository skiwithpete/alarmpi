#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import argparse
import importlib

import pydub
import pydub.playback
import alarmenv

# Loop throught the configuration file for enabled components and
# intantiate corresponding classes for processing the sections.

# 1 create an alarmenv and parse configs
# 2 create necessary handlers

# Create mapping between a handler module name and class names for those handlers
handler_map = {
    "get_google_translate_tts": "GoogleTranslateTTSManager",
    "get_festival_tts": "FestivalTTSManager",
    "get_greeting": "Greeting",
    "get_bbc_news": "NewsParser",
    "get_textfile": "TextFileParser",
    "get_yahoo_weather": "YahooWeatherClient"
}


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

    if alarm_env.debug:
        for section in contents:
            print(section)
            print()

    return contents


def get_tts_client(alarm_env):
    """Determine which TTS engine to use based on the enabled tts sections
    in the config file. First enabled section is used.
    """
    tts = [s for s in alarm_env.get_sections(exclude_main=True) if
           alarm_env.config_has_match(s, "type", "tts") and
           alarm_env.config_has_match(s, "enabled", "1")
           ]
    if tts:
        tts_section = tts[0]
        class_ = get_content_parser_class(alarm_env, tts_section)
        client = class_()

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Play the alarm using a specified configuration file')
    parser.add_argument('config', metavar='config', nargs='?',
                        default='alarm.config', help='path to the config file')
    parser.add_argument('--init-config', action="store_true",
                        help="re-create the default configuration file alarm.config. Overwrites existing file.")
    parser.add_argument('debug', action='store_true', help='prints debug messages during execution')
    args = parser.parse_args()

    alarm_env = alarmenv.AlarmEnv(args.config, args.debug)
    if args.init_config:
        alarm_env.write_default_configuration()

    # Check status for internet connection. If no connection detected,
    # play a beeping sound instead of making API calls.
    if not alarm_env.netup:
        beep = pydub.AudioSegment.from_mp3("resources/Cool-alarm-tone-notification-sound.mp3")
        pydub.playback.play(beep)

    content = generate_content(alarm_env)

    tts_enabled = alarm_env.config_has_match("main", "readaloud", "1")
    if tts_enabled:
        tts_client = get_tts_client(alarm_env)
        text = "\n".join(content)
        tts_client.play(text)

    # If TTS is not enabled, print the contents, unless debug mode is set,
    # in which case the contents are already printed.
    # TODO should beeper play if readaloud disabled?
    elif not alarm_env.debug:
        for section in content:
            print(section)
            print()

    radio_enabled = alarm_env.config_has_match("radio", "enabled", "1")
    if radio_enabled:
        url = alarm_env.get_value("radio", "url")
        cmd = "/usr/bin/mplayer -nolirc -playlist {}".format(url).split()
        subprocess.run(cmd)
