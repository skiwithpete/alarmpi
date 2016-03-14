#!/bin/python
# -*- coding: utf-8 -*-

from apcontent import alarmpi_content

class textfile(alarmpi_content):

  def build(self):
    textfile = 'Textfile enabled but file could not be read.'

    try:
      with open(self.sconfig['filepath'], 'r') as myfile:
        textfile=myfile.read().replace('\n', '  ')
    except IOError:
      pass

    if self.debug:
      print textfile

    self.content = textfile
