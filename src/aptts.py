import pydub.playback


class AlarmpiTTS:
    """Base class for TTS clients. Provide a common credentials argument
    and an abstract method for initializing the actual TTS client.
    """

    def __init__(self, credentials=None):
        self.credentials = credentials

    def setup(self, text):
        """Setup any TTS client and make requests to transform text as audio
        content to be played.
        Args:
            text (string): the textual content to be processed by the actual TTS client.
        Return:
            Audio content to be played as pydub.AudioSegment
        """
        raise NotImplementedError

    def play(self, audio):
        """Play audio content.
        Args:
            audio (pydub.AudioSegment): prebuilt content to be played
        """
        pydub.playback.play(audio)
