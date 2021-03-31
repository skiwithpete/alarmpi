#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.cloud import texttospeech
from google.oauth2 import service_account

from src import aptts


class GoogleCloudTTS(aptts.AlarmpiTTS):
    """A Google Cloud Text-to-Speech client. This uses a WaveNet voice for more human-like
    speech and higher costs. However, the monthly free tier of 1 million charaters
    should easily cover the requirements for running the alarm once a day.

    For API limits and pricing, see
    https://cloud.google.com/text-to-speech/quotas
    https://cloud.google.com/text-to-speech/pricing
    """

    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.client = self.get_client()

    def get_client(self):
        """Create an API client using a path to a service account key_file."""
        try:
            credentials = service_account.Credentials.from_service_account_file(self.credentials)
            client = texttospeech.TextToSpeechClient(credentials=credentials)
        except FileNotFoundError:
            raise RuntimeError(
                "Error using Google Speech: couldn't read keyfile {}".format(self.credentials))
        return client
