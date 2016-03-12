#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

from apeffect import alarmpi_effect

class music(alarmpi_effect):
  # Don't do anything at the beginning
  def begin(self):
    pass

  # Play a song at the end
  def end(self):
    print subprocess.call ('find '+
                            self.sconfig['musicfldr'] +
                            ' -name \'*' +
                            self.sconfig['tail'] + '\' | sort --random-sort| ' +
                            self.sconfig['player'],
                            shell=True)

