#!/bin/bash

# Create a copy of alarm.config and remove write access to work as
# default configuration file.
# This script is mainly for development purposes, it's not much use
# if run after alarm.config is modified

rm default.config
cp alarm.config default.config
echo -e "# This is a read-only copy of a default alarm configuration file.\n# Use to restore original settings\n\n$(cat alarm.config)" > default.config

chmod a-w default.config
