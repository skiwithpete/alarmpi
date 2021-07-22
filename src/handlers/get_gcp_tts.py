import io

import pydub
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

    def play(self, text):
        """Create a TTS client and speak input text using pydub."""
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
        response = self.client.synthesize_speech(synthesis_input, voice, audio_config)

        # create a BytesIO buffer and play via pydub
        f = io.BytesIO(response.audio_content)
        audio = pydub.AudioSegment.from_file(f, format="mp3")
        pydub.playback.play(audio)