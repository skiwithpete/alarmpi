#!/bin/python
# -*- coding: utf-8 -*-

import apcontent


class TextFileParser(apcontent.AlarmpiContent):

    def build(self):
        textfile = 'Textfile enabled but file could not be read.'

        try:
            with open(self.sconfig['filepath'], 'r') as f:
                textfile = f.read().replace('\n', '  ')
        except IOError:
            pass

        self.content = textfile
