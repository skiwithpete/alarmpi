
#!/bin/python
# -*- coding: utf-8 -*-
import time
import better_spoken_numbers as bsn

from apcontent import alarmpi_content

#print int(time.strftime("%m%d"))

class birthday(alarmpi_content):

  def build(self):
    birthday = None

    if int(time.strftime("%m%d")) == 929 :
      birthday = 'Ski with Pete'
    #if int(time.strftime("%m%d")) == 129 :
    #  birthday = 'dummy'

    # reads out birthday
    if birthday is None:
      birthday = 'I dont know of anyone having a birthday today.  '
    else:
      birthday = 'Today is ' + birthday + 's birthday.  ' 

    if self.debug:
      print birthday

    self.content = birthday
