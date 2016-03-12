#!/usr/bin/env python
# -*- coding: utf-8 -*-

class alarmpi_section:
  def __init__(self, stype, sconfig, debug, main):
    self.stype = stype
    self.sconfig = dict(sconfig)
    self.main = dict(main)
    self.debug = debug

  def standalone(self):
    sconfig = self.sconfig
    return 'standalone' in sconfig and sconfig['standalone'] == str(1)
