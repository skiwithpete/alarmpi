#!/usr/bin/env python
# -*- coding: utf-8 -*-
from apsection import alarmpi_section

class alarmpi_tts(alarmpi_section):

  def play(self, content, ramdrive='/mnt/ram/'):
    self.content='Instance of ' + \
                 self.stype + \
                 ' class play method called with:\n\n\t' + \
                 content
    print self.content
    return False
