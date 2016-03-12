#!/usr/bin/env python
# -*- coding: utf-8 -*-
from apsection import alarmpi_section

class alarmpi_effect(alarmpi_section):

  # Do this at the beginning of the alarm
  def begin(self):
    print 'Instance of ' + self.stype + ' class begin method.'

  # Do this at the end of the alarm
  def end(self):
    print 'Instance of ' + self.stype + ' class end method.'
