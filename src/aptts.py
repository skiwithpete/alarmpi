class AlarmpiTTS:
    """Base class for TTS clients. Provide a common credentials argument
    and an abstract method for initializing the actual TTS client.
    """

    def __init__(self, credentials=None):
        self.credentials = credentials

    def setup(self, text):
        """This function should make any required API setup, such as
        TTS client creation as well as the actual API calls.
        Once subclassed, this function should return something than can be passed
        to pydub to play (ie. pydub.AudioSegment).
        Args:
            text (string): the textual content to be processed by the actual TTS client.
        Return:
            Audio content to be played. Something to pass to pydub, such as pydub.AudioSegment
        """
        raise NotImplementedError
