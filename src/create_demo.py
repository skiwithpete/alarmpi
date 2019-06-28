#!/usr/bin/env python
# -*- coding: utf-8 -*-

import alarm_builder
import alarmenv
import handlers.get_gcp_tts

"""Creates a demo alarm with greeting, weather and news and stores as an mp3 file."""


if __name__ == "__main__":
    alarm_env = alarmenv.AlarmEnv("alarm.config")
    content = alarm_builder.generate_content(alarm_env)
    text = "\n".join(content)

    tts = handlers.get_gcp_tts.GoogleCloudTTS(keyfile="Alarmpi-cdb50622e298.json")
    tts.synthesize_and_store(text)
