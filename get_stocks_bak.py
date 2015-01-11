#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
import decimal
import ConfigParser
import better_spoken_numbers as bsn
from math import floor

Config=ConfigParser.ConfigParser()
try:
  Config.read('alarm.config')
except:
  raise Exception('Sorry, Failed reading alarm.config file.')

tickers=Config.get('stocks','tickers').split(',')

stocks='Stock update: '

for ticker in tickers:
  try: 
    api = urllib2.urlopen('http://finance.yahoo.com/webservice/v1/symbols/'+ticker+'/quote?format=json', timeout=4)
    response = api.read()
    response_dictionary = json.loads(response)
    stock_name = response_dictionary['list']['resources'][0]['resource']['fields']['name'].replace("Common Stock", '').replace(' Inc','').replace(',','').replace('.','').replace('(NS) O','')

    # get the price
    stock_price = response_dictionary['list']['resources'][0]['resource']['fields']['price']
    # trim it to something sane
    stock_price = round(decimal.Decimal(stock_price),2)

    whole_price = floor(stock_price)
    decimal_price = floor((stock_price - whole_price)*100)
    stock_price = bsn.n2w(int(whole_price)) + ' dollars'
    if decimal_price > 0:
      stock_price += ' and ' + bsn.n2w(int(decimal_price)) + ' cents'
    
    stocks += stock_name + ' is trading at ' + stock_price + '.  '
    
  except Exception:
    stocks = 'Failed to connect to Yahoo Finance.  '

if Config.get('main','debug') == str(1):
  print stocks
