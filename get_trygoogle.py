#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import textwrap

from aptts import alarmpi_tts

class trygoogle(alarmpi_tts):
  def play(self, content, ramdrive='/mnt/ram/'):
    rval = True
    # Google voice only accepts 100 characters or less, so split into chunks
    shorts = []

    gturl = 'http://' + \
            self.sconfig['host'] + \
            self.sconfig['path'] + \
            '?tl=' + \
            self.sconfig['lang']

    gtclient = '&client=' + self.sconfig['client']

    head = self.sconfig['head']
    tail = self.sconfig['tail']

    for chunk in content.split('.  '):
      shorts.extend(textwrap.wrap(chunk, 100))

    count = 0
    play = 'Unassigned'
    # Send shorts to Google and return mp3s
    try:
      for sentence in shorts:
        sendthis = sentence.join([' "' +
                                  gturl +
                                  '&q=',
                                  gtclient +
                                  '" -O ' +
                                  ramdrive])

        st = head + sendthis + str(count).zfill(2) + str(tail)
        if self.debug:
          print(st)
        print subprocess.call (st, shell=True)
        count = count + 1

      # Play the mp3s returned
      play = self.sconfig['player'] + ' ' + ramdrive + '*' + tail
      if self.debug:
        print 'Calling "' + play + '"'
      print subprocess.call (play, shell=True)
    except:
      rval = False

    # Cleanup any mp3 files created in this directory.
    rmcmd = 'rm -f ' + ramdrive + '*.' + tail
    if self.debug:
      print 'cleaning up now'
      print rmcmd
    print subprocess.call (rmcmd, shell=True)
    return rval
