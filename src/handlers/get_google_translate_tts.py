#!/usr/bin/env python
# -*- coding: utf-8 -*-
import textwrap
import requests
import io

import pydub
import pydub.playback

from src import aptts


class GoogleTranslateTTSManager(aptts.AlarmpiTTS):
    """A Google Translate API's text-to-speech client.
    Note the Translate API is unofficial and undocumented and may break at any time. The
    parameters are mostly gathered from various StackOverflow posts, such as
    https://stackoverflow.com/questions/35002003/how-to-use-google-translate-tts-with-the-new-v2-api
    """

    def play(self, text):
        """Send text to the translate_tts API and play results.
        The API only accepts 200 characters per requests.
        Split the text to part, send request for each and play all results
        after the requests to minimize processing delays.
        """
        url = "https://translate.google.com/translate_tts"

        parts = textwrap.wrap(text, 200)
        audio = pydub.AudioSegment.empty()  # init an empty AudioSegment as base for appending other segments
        for part in parts:
            params = {
                "tl": "en",
                "client": "tw-ob",
                "ie": "UTF-8",
                "q": part
            }
            r = requests.get(url, params=params)  # response is an mp3 file as a byte string
            f = io.BytesIO(r.content)
            audio_part = pydub.AudioSegment.from_file(f, format="mp3")
            audio += audio_part

        pydub.playback.play(audio)

    def play_sample(self):
        url = "https://translate.google.com/translate_tts"

        params = {
            "tl": "en",
            "client": "tw-ob",
            "ie": "UTF-8",
            "q": "Some sort of monster, I guess."
        }
        r = requests.get(url, params=params)  # response is an mp3 file
        f = io.BytesIO(r.content)
        audio1 = pydub.AudioSegment.from_file(f, format="mp3")

        params = {
            "tl": "en",
            "client": "tw-ob",
            "ie": "UTF-8",
            "q": "Next time is never before the beginning"
        }
        r = requests.get(url, params=params)  # response is an mp3 file
        f = io.BytesIO(r.content)
        audio2 = pydub.AudioSegment.from_file(f, format="mp3")

        audio = audio1 + audio2
        pydub.playback.play(audio)
