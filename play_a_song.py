#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import subprocess

Config=ConfigParser.ConfigParser()
try:
  Config.read('alarm.config')
except:
  raise Exception('Sorry, Failed reading alarm.config file.')

subprocess.call('find '+ Config.get('main','musicfldr') + ' -name \'*.mp3\' | sort --random-sort| mpg123 -@ - -l 1 -g 60', shell=True)