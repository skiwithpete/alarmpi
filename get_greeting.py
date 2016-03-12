#!/bin/python
# -*- coding: utf-8 -*-
import time
import better_spoken_numbers as bsn

from apcontent import alarmpi_content

class greeting(alarmpi_content):
  def build(self):
    day_of_month=str(bsn.d2w(int(time.strftime("%d"))))

    now = time.strftime("%A %B ") + day_of_month + ',' + time.strftime(" %I %M %p")

    if int(time.strftime("%H")) < 12:
      period = 'morning'
    if int(time.strftime("%H")) >= 12:
      period = 'afternoon'
    if int(time.strftime("%H")) >= 17:
      period = 'evening'

    # reads out good morning + my name
    gmt = 'Good ' + period + ', '

    # reads date and time 
    day = ' it\'s ' + now + '.  '

    greeting = gmt + self.sconfig['name'] + day

    if self.debug:
      print greeting

    self.content = greeting
