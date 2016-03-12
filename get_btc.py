#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json
import better_spoken_numbers as bsn
from math import floor

from apcontent import alarmpi_content

class btc(alarmpi_content):
  def build(self):
    try: 
      coinbase_url = 'https://' + self.sconfig['host'] + self.sconfig['path']
      coinbase_api = urllib.urlopen(coinbase_url)
      response = coinbase_api.read()
      response_dictionary = json.loads(response)
      # reads bit coin value from coinbase
      btc_price=response_dictionary['subtotal']['amount']
      whole_price = int(floor(float(btc_price)))
      decimal_price = int(floor((float(btc_price) - whole_price)*100))
      btc_price = bsn.n2w(int(whole_price)) + ' dollars'
      if decimal_price > 0:
        btc_price += ' and ' + bsn.n2w(int(decimal_price)) + ' cents'

      btc = 'The value of 1 bitcoin is: ' + btc_price + '.  '
    except Exception:
      btc = 'Failed to connect to coinbase.  '

  #print response_dictionary['amount']
  #print response_dictionary['subtotal']['amount']

    if self.debug:
      print btc

    self.content = btc
