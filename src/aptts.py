class AlarmpiTTS:
    """Helper base class for tts clients. Sets path to key file as an attribute
    for tts clients that require one and lists an abstract play method for
    tts engine specific clients to implement.
    """

    def __init__(self, credentials=None):
        self.credentials = credentials

    def play(self, text):
        """This function should translate the input text to speech and play it.
        Its implementation depends on the API of the engine used.
        """
        raise NotImplementedError
