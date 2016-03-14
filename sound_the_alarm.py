#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
import subprocess

import alarmenv

# Read the system configuration
AlmEnv=alarmenv.alarmEnv()

# Holds the class instances of each individual section by type
sections = {
  "content": OrderedDict(),
  "effect": OrderedDict(),
  "tts": OrderedDict()
}

wadparts=[]

for section in AlmEnv.sections():
  # We are going to pass only the main and section specific
  # parts of the configuration to the section modules
  mainitems = AlmEnv.items('main')
  # We'll add the net state to the main section
  mainitems.extend((('netup',AlmEnv.netup),))
  if (section != 'main' and
      AlmEnv.hasAndIs(section, 'enabled', 1)):
    try:
      handler = AlmEnv.handler(section)
      getsec = 'get_' + handler
      # Section type -- one of 'effect' 'content' 'tts'
      stype = AlmEnv.stype(section)
      # AlmEnv options specific to this section
      items  = AlmEnv.items(section)
      # Get the constructor
      construct = getattr(__import__(getsec, fromlist=[handler]), handler)
      # Construct an instance and put it in out holder
      sections[stype][section]=construct(stype,items,AlmEnv.debug,mainitems)
      if stype == 'content':
        wadparts.extend(sections[stype][section].get(AlmEnv.netup) + "   ")
    except ImportError:
      raise ImportError('Failed to load '+section)

count = 1

# Do the Begin part of all effects
for ename in sections['effect']:
  if AlmEnv.debug:
    print ename
  sections['effect'][ename].begin()

# Turn all of the parts into a single string
wad = (''.join(str(x) for x in wadparts) + AlmEnv.get('main','end'))

if AlmEnv.debug:
  print wad

if AlmEnv.get('main','readaloud') == str(1):
  # strip any quotation marks
  wad = wad.replace('"', ' ').replace("'",' ').strip()

  # Try to speak the text
  played = False
  for tname in sections['tts']:
    if AlmEnv.debug:
      print tname + ':' + str(played)
    if not played: # don't try unless we haven't played
      played = sections['tts'][tname].play(wad)

  if not played: # Nothing worked, so try festival
    print subprocess.call("echo " + wad + " | festival --tts ", shell=True)
  
else:
  print wad

# Do the End part of all effects (in the reverse order they were started)
effects = sections['effect'].items()
effects.reverse()
for effect in effects:
  if AlmEnv.debug:
    print effect
  effect[1].end()
