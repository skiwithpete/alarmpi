#!/usr/bin/env python
# -*- coding: utf-8 -*-


class AlarmpiContent:
    """Helper base class for all handlers. Defines functions for creating an actual
    handler from a particular section read from the configuration file. The build
    function should be implemented in each subclass.
    """

    def __init__(self, section_data):
        """Create a an abstract content handler.
        Args:
            section_data (configparser.SectionProxy): a section of the configuration file
                as parsed by a configparser, ie. config["greeting"]
        """
        self.section_data = section_data
        self.content = None

    def get(self):
        """convenience method for returning the contents."""
        return self.content

    def build(self):
        """This function should store the value to pass to the TTS client as the
        'content' attribute as a string. For reference, see handlers/get_greeting.py.
        """
        raise NotImplementedError
