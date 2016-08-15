#!/usr/bin/env python
# -*- coding: utf-8 -*-
from apsection import alarmpi_section

class alarmpi_content(alarmpi_section):
  def __init__(self, stype, sconfig, debug, main):
    alarmpi_section.__init__(self, stype, sconfig, debug, main)
    self.build()

  def get(self, netup):
    if(self.main['netup']):
      if self.standalone() < 2:
        return self._get()
      else:
        return ' ' # standalone > 1 means standalone only
    else:
      if self.standalone() < 2:
        return self._get_offline()
      return self._get() # standalone > 1 means standalone only

  def _get(self):
    return self.content

  def _get_offline(self):
    return self.content + '  ().  '

  def build(self):
    self.content='Instance of ' + self.stype + ' class.'
