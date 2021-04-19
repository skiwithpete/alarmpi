#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Creates a demo alarm with greeting, weather and news and stores as an mp3 file.

from google.cloud import texttospeech
from google.oauth2 import service_account

from src import alarm_builder, alarmenv
from src.handlers import get_gcp_tts


client = texttospeech.TextToSpeechClient()


def synthesize_and_store(text):
    """Synthesize speech and store as mp3 file for demonstration purposes."""
    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    # Build the voice request and specify a WaveNet voice for more human like speech
    voice = texttospeech.types.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-C"
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)
    with open("demo.mp3", "wb") as f:
        f.write(response.audio_content)


if __name__ == "__main__":
    env = alarmenv.AlarmEnv("default.conf")
    env.setup()
    builder = alarm_builder.Alarm(env)
    content = builder.build()
    text = "\n".join(content)
    synthesize_and_store(text)
