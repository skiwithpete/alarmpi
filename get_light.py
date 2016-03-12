#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import time

from apeffect import alarmpi_effect

class light(alarmpi_effect):
  def __init__(self, stype, sconfig, debug,main):
    alarmpi_effect.__init__(self, stype, sconfig, debug,main)
    self.delay = int(self.sconfig['delay'])

  def begin(self):
    print subprocess.call ('python lighton_1.py', shell=True)

  def end(self):
    time.sleep(self.delay)
    print subprocess.call ('python lightoff_1.py', shell=True)
