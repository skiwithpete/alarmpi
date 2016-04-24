#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import subprocess
import uuid

from aptts import alarmpi_tts

class trypico2wave(alarmpi_tts):
  def play(self, content, ramdrive='/mnt/ram/'):
    if self.debug:
      print "Trying pico2wave."
    rval = True
    p2w = self.sconfig['head']
    lang =self.sconfig['lang']
    if not os.path.isfile(p2w): # The executable does not exist
      if self.debug:
        print 'File ' + p2w + ' does not exist.'
      return False
    try:
      tmfn = ramdrive + str(uuid.uuid4()) + self.sconfig['tail']
      cmd = p2w + ' -l ' + lang + ' -w ' + tmfn + ' "' + content + '"'
      if self.debug:
        print cmd
      print subprocess.call(cmd, shell=True)
      cmd = self.sconfig['player'] + ' ' + tmfn
      if self.debug:
        print cmd
      print subprocess.call(cmd, shell=True)
      cmd = 'rm -f ' + tmfn
      if self.debug:
        print cmd
      print subprocess.call(cmd, shell=True)
    except subprocess.CalledProcessError:
      rval = False
      
    # Cleanup any ogg files created in this directory.
    if self.debug:
      print 'cleaning up now'
    rmcmd = 'rm -f ' + ramdrive + '*' + self.sconfig['tail']
    if self.debug:
       print rmcmd
    print subprocess.call (rmcmd, shell=True)
  
    return rval
