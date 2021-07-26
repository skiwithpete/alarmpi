class AlarmpiContent:
    """Base class for alarm content parsers. Defines functions for creating an actual
    handler from a particular section read from the configuration file.
    """

    def __init__(self, section_data):
        """Create a an abstract content handler.
        Args:
            section_data: a section of the configuration file defining this content
        """
        self.section_data = section_data
        self.content = None

    def get(self):
        return self.content

    def build(self):
        """Builds this content. To be implemented in subclass.
        This function should return a string which is to be passed to the TTS client
        as part of the alarm.
        For reference see, implementation in handlers/get_greeting.py.
        """
        raise NotImplementedError
