#!/usr/bin/python
from math import floor

num2words = {0: 'Zero ', 1: 'One ', 2: 'Two ', 3: 'Three ', 4: 'Four ', 5: 'Five ',
             6: 'Six ', 7: 'Seven ', 8: 'Eight ', 9: 'Nine ', 10: 'Ten ',
            11: 'Eleven ', 12: 'Twelve ', 13: 'Thirteen ', 14: 'Fourteen ',
            15: 'Fifteen ', 16: 'Sixteen ', 17: 'Seventeen ', 18: 'Eighteen ',
            19: 'Nineteen ', 20: 'Twenty ', 30: 'Thirty ', 40: 'Forty ',
            50: 'Fifty ', 60: 'Sixty ', 70: 'Seventy ', 80: 'Eighty ',
            90: 'Ninety '}

date2words = {1: 'First', 2: 'Second', 3: 'Third', 4: 'Fourth', 5: 'Fifth',
            6: 'Sixth', 7: 'Seventh', 8: 'Eighth', 9: 'Ninth', 10: 'Tenth',
           11: 'Eleventh', 12: 'Twelfth', 13: 'Thirteenth', 14: 'Fourteenth',
           15: 'Fifteenth', 16: 'Sixteenth', 17: 'Seventeenth', 18: 'Eighteenth',
           19: 'Nineteenth', 20: 'Twentieth', 30: 'Thirtieth'}

def n2w(n):
  if n<=20:
    return num2words[n]
  elif n<100:
    words=num2words[n-n%10]
    if n%10>0:
      words+=num2words[n%10]
    return words
  elif n<1000:
    hundreds=(n-n%100)/100
    tens=(n%100)-(n%100)%10
    singles=n-((hundreds*100)+tens)
    words=num2words[hundreds] + ' hundred'
    if tens > 0:
      words+=' '+num2words[tens]
    if singles > 0:
      words+=num2words[singles]
    return words
  elif n<1000000:
    thousands=(n-n%1000)/1000
    remainder=n-(thousands*1000)
    words=n2w(thousands)+' thousand'
    if remainder>0:
      words+=' '+n2w(remainder)
    return words
  elif n<1000000000:
    millions=(n-n%1000000)/1000000
    remainder=n-(millions*1000000)
    words=n2w(millions)+' million'
    if remainder>0:
      words+=' '+n2w(remainder)
    return words
  else:
    return 'Number out of range'

def d2w(n):
  try:
    return date2words[n]
  except KeyError:
    try:
      return num2words[n-n%10] + date2words[n%10]
    except KeyError:
      return 'Date out of range'


