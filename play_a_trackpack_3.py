#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import subprocess
import time

Config=ConfigParser.ConfigParser()
try:
  Config.read('alarm.config')
except:
  raise Exception('Sorry, Failed reading alarm.config file.')

if Config.get('main','light') == str(1):
  print subprocess.call ('python lighton_1.py', shell=True)

subprocess.call('find '+ Config.get('main','musicfldr') + ' -name \'*.mp3\' | sort --random-sort| head -n 3| xargs -d \'\n\' mpg123', shell=True)

if Config.get('main','light') == str(1):
  time.sleep(int(Config.get('main','lightdelay')));
  print subprocess.call ('python lightoff_1.py', shell=True)