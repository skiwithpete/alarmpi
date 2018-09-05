# Alarmpi

A clock radio for a Raspberry Pi with a display, work in progress.

This is a fork of skiwithpete's alarmpi project: https://github.com/skiwithpete/alarmpi. After seeing it on [YouTube](https://youtu.be/julETnOLkaU), I knew wanted to build a similar system to replace my existing bedside clock radio. I had already bought the official touchscreen with a new Pi but other than messing around with it, I had no real use for it until this project.

### Main Features
 * A greeting based on time of day
 * Tells the day's weather using Yahoo Weather
 * Reads latest news from BBC World RSS feeds

 These are largely the same as the corresponding features in the original project. Additionally I've added two new one for my own use case:
 * A GUI for displaying current time as well as for scheduling the alarm.

  * The GUI is rather primitive due to hardware limitations: I build this project to run on a Raspberry Pi together with the official touch screen display with no additional input device. Since Raspbian is not a touch screen OS, it's support is limited to emulating mouse clicks. The alarm is therefore set using a binary based system for the hour and minute. TODO: image

 * Stream a radio station using `mplayer`


I've made a number of changed to the original project:
 * Ported the project Python 3 (Python 2 is unsupported)
 * changed naming conventions to be more PEP 8 compliant and other minor cleanups
 * Cleaned up file structure
 * Removed some modules I deemed unnecessary (mainly due to removed features, see the next point)
 * Removed features not applicable to my use case (including turning lights on and off, playing songs and reading stocks from Yahoo Finance, which has been discontinued)
 * Changed which text-to-speech engines are available, see below
 * Changed audio processing to use in-memory objects, thus removing the need to setup a ramdrive
 * Added unit tests (although the test suite is a bit light)



### Setup
Run `sh setup.sh` to install required system packages. This includes the Festival text-to-speech engine and some libraries enabling audio processing directly in Python.

Install requires Python packages with `pip install -r requirements.txt`. Using a virtualenv is recommended.

Optionally, run unit tests with `python tests/test_alarm.py`


### Usage
Run the program with `python main.py`. This opens the GUI for displaying current time and scheduling the alarm.

You can also run the alarm directly with `python sound_the_alarm.py`. This parses the configuration file (by default `alarm.config`), creates an approriate alarm and plays it.
```
positional arguments:
  config         path to the config file
  debug          prints debug messages during execution

optional arguments:
  -h, --help     show this help message and exit
  --init-config  re-create the default configuration file alarm.config.
                 Overwrites existing file.
```
TODO: run instructions, tts-setup

#### alarm.config description

#### Extending alarm.config with more content
