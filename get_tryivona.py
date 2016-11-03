#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pyvona
import pygame
import subprocess
import utilities

from aptts import alarmpi_tts

class tryivona(alarmpi_tts):
  def play(self, content, ramdrive='/mnt/ram/'):
    if self.debug:
      print "Trying Ivona."
    rval = True
    try:
      #Connect to Ivona
      v = pyvona.create_voice(self.sconfig['ivona_accesskey'],
                              self.sconfig['ivona_secretkey'])
      #Settings for ivona
      v.voice_name = self.sconfig['ivona_voice']
      v.speech_rate = self.sconfig['ivona_speed']
      #Get ogg file with speech
      content = utilities.stripSymbols(content) # Removes symbols before sending to Ivona
      v.fetch_voice(content, ramdrive + 'tempspeech.ogg')
      
      # Play the oggs returned
      pygame.mixer.init()
      pygame.mixer.music.load(ramdrive + "tempspeech.ogg")
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy() == True:
        continue
        
    except pyvona.PyvonaException:
      rval = False

    except subprocess.CalledProcessError:
      rval = False
      
    # Cleanup any ogg files created in this directory.
    print 'cleaning up now'
    rmcmd = 'rm -f ' + ramdrive + '*' + self.sconfig['tail']
    print subprocess.call (rmcmd, shell=True)
  
    return rval
