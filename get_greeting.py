#!/bin/python
# -*- coding: utf-8 -*-
import time
import better_spoken_numbers as bsn
import ConfigParser

Config=ConfigParser.ConfigParser()
try:
  Config.read('alarm.config')
except:
  raise Exception('Sorry, Failed reading alarm.config file.')

day_of_month=str(bsn.d2w(int(time.strftime("%d"))))

now = time.strftime("%A %B ") + day_of_month + ',' + time.strftime(" %I %M %p")
# print now


if int(time.strftime("%H")) < 12:
  period = 'morning'
if int(time.strftime("%H")) >= 12:
  period = 'afternoon'
if int(time.strftime("%H")) >= 17:
  period = 'evening'

#print time.strftime("%H")
#print period

# reads out good morning + my name
gmt = 'Good ' + period + ', '

# reads date and time 
day = ' it\'s ' + now + '.  '

greeting = gmt + Config.get('greeting','name') + day

if Config.get('main','debug') == str(1):
  print greeting