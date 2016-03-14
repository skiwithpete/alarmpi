#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import ConfigParser
import dns.resolver
import os
import sys

# Class that keeps track of the execution environment
#   (configuration + system state)
class alarmEnv:
  defaults = {
    ###################
    # Config defaults #
    ###################

    # These can be overriden in the [main] config section
    # Default config filename
    'ConfigFile': 'alarm.config',

    # Default host to try to test network connectivity
    'nthost': 'translate.google.com',
  }

  def __init__(self):
    # Change to our script directory if we can
    self.startpath=os.getcwd()
    stapath = os.path.dirname(sys.argv[0])
    if stapath:
      os.chdir(stapath) # When called from cron, we can find our code

    self.Config=ConfigParser.SafeConfigParser()

    # Take command line arguments
    parser = argparse.ArgumentParser()

    # Debug can be set in either the config file or in the command line.
    parser.add_argument("--debug",
                        help="output debug info",
                        action="store_true")

    # Use a config file other than the default (allows distinct alarms)
    parser.add_argument("--config", help="specify the config file")

    args = parser.parse_args()

    ConfigFile = self._getConfigFileName(args.config)
    try:
      self.Config.read(ConfigFile)
    except:
      raise Exception('Sorry, Failed reading config file: ' + ConfigFile)

    # Cheap partial inheritence. Blame Craig.
    self.get = self.Config.get
    self.has_option = self.Config.has_option
    self.sections = self.Config.sections
    self.items = self.Config.items

    # Debug can be set in either the config file or in the command line.
    self.debug = args.debug or self.hasAndIs('main','debug',1)

    # We still want to alarm if the net is down
    self._testnet()


  # get a config file name, resolving relative path if needed
  def _getConfigFileName(self,fname):
    if fname:
      if not os.path.isabs(fname):
        return os.path.abspath(os.path.join(self.startpath,fname))
      return fname
    else:
      return self.defaults['ConfigFile']

  def _getDefault(self,o,s='main'):
    if self.Config.has_option(s,o):
      return self.Config.get(s,o)
    return self.defaults[o]
  
  def _testnet(self):
    # Test for connectivity
    nthost = self._getDefault('nthost')
    try:
      dns.resolver.query(nthost)
      self.netup=True
    except:
      self.netup = False                                                              
      if self.debug:
        print('Could not resolve "' +
              nthost +
              '". Assuming the network is down.')

  # Boolean, returns False unless Config has a Section/Option that
  # matches the value
  def hasAndIs(self,s,o,v):
    return self.has_option(s,o) and (self.get(s,o) == str(v))

  def stype(self,s):
    return self.Config.get(s,'stype')

  # This allows for multiple sections to use the same class
  # (distinct instances) to handle the work
  def handler(self,s):
    if self.has_option(s,'handler'):
      return self.get(s,'handler')
    return s
