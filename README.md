# Alarmpi

A Raspberry Pi clock radio with customizable Text To Speech alarm.
```
Good afternoon, it's Wednesday September twelfth. The time is 07:29 PM.

Weather for today is Mostly Cloudy becoming rainy. It is currently 16 degrees  with a fresh breeze. The high for today is 17 and the low at 11 degrees. The sun rises at 06:43 AM and sets at 07:50 PM.

And now, The latest stories from the World section of the BBC News.

EU parliament votes to punish Hungary over 'breaches' of core values.
The European Parliament votes to punish Hungary for allegedly flouting EU values and the rule of law.

Hurricane Florence: Mass evacuation from 'storm of a lifetime'.
South Carolina authorities turn four motorways into one-way routes away from the coast.

Morocco bans forced marriage and sexual violence.
The new law criminalises sexual harassment and imposes tougher penalties on perpetrators.

Sri Lanka to ban Hindu animal sacrifice.
The ritual killing of animals such as goats could soon be outlawed at Sri Lanka's Hindu temples.


Thats all for now. Have a nice day.
```
[Play on SoundCloud](https://soundcloud.com/lajanki/pialarm_sample)


This is a fork of skiwithpete's alarmpi project: https://github.com/skiwithpete/alarmpi. After seeing it on [YouTube](https://youtu.be/julETnOLkaU), I thought it was neat and knew I wanted to use it to replace my old night table clock radio.


### Main Features
 * A spoken greeting based on time of day
 * Reads the day's weather from openweathermap.org
 * Reads latest news from BBC World RSS feed
 * Plays internet radio streams
 * Alarm scheduling via cron
 * A PyQt5 based GUI


![Main window](resources/clock_main.png)

![schedule window](resources/clock_schedule.png)


### Hardware setup
This project is built around the following hardware.
 * Raspberry Pi
 * Official Raspberry Pi Display
 * A speaker

Apart from the speaker these aren't requirements per se. The project is mostly a couple of Python scripts which will likely run on many Linux platforms. The GUI does have two bindings to a Raspberry Pi: the buttons for toggling screen brightness and putting it to sleep are disabled on a different system.

It's also possible to run the alarm without the GUI on a headless setup, see Usage below.



### Setup
 1. First, install required system packages with

  ```apt install ffmpeg festival mplayer portaudio19-dev python-all-dev```

  These include the Festival text-to-speech engine, the command line movie player mplayer and audio libraries enabling playback of mp3 files directly in Python.

 2. Next, install required Python packages.

 These can either be installed inside a virtualenv or directly under system Python. While using a virtualenv is recommended, using one does come with an extra step when the target system is a Raspberry Pi. This project is buit using PyQt5, a GUI library for which there is no PyPI package available for ARM platforms (at the time of writing, March 5th, 2019), so it cannot be installed with pip. Instead PyQt5 needs to be compiled from source, see below.

 Thus, options for installing Python packages include:

 **Raspberry Pi with virtualenv**
  1. Create and activate the environment with
 ```
 python3 -m virtualenv venv
 source venv/bin/activate
 ```
  2. Download SIP  
  https://www.riverbankcomputing.com/software/sip/download  
  According to the documentation, SIP is a
  > tool that makes it very easy to create Python bindings for C and C++ libraries. It was originally developed to create PyQt, the Python bindings for the Qt toolkit, but can be used to create bindings for any C or C++ library.

  3. Extract the archive and build the module
     ```
     tar -xvf sip-4.19.14.tar.gz
     python sip-4.19.14/configure.py --sip-module PyQt5.sip --no-tools
     make
     sudo make install
     sudo make clean
     ```
  4. Download PyQt5  
  https://riverbankcomputing.com/software/pyqt/download5  

  5. Extract and build
     ```
     tar -xvf PyQt5_gpl-5.12.tar.gz
     python PyQt5_gpl-5.12/configure.py
     make
     sudo make install
     sudo make clean
     ```
     This will take a long time!

  6. Finally, install the rest of Python packages via `pip`:
  ```
  pip install -r requirements.txt
  ```

 **Raspberry Pi with system Python**
  1. Outside a virtualenv PyQt5 can be installed as a system package with `apt`:
  ```
  apt update
  apt install python3-pyqt5
  ```
  2. Install the rest of Python packages via `pip`:
  ```
  pip install -r requirements.txt
  ```

 **Ubuntu, x86**
  1. on a non-arm machine, everything can be installed directly with `pip`
  ```
  pip install pyqt5
  pip install -r requirements.txt
  ```
 3. After Python requirements are installed, initialize crontab with `crontab -e` and follow the instructions (if you haven't done so already).
   * `cron` is used to schedule the alarm. You may want to create a backup of an existing crontab with
   ```
   crontab cron.backup
   ```
   before running the script. It can be restored with
   ```
   crontab -l > cron.backup
   ```

 4. Optionally, run unit tests with

  ```python -m unittest -v tests/test*.py```


### Usage
Run the script either with
```
python main.py [path/to/configuration/file]
```
or
```
python alarm_builder.py [path/to/configuration/file]
```

The first runs a GUI version. It displays the current time and includes options for scheduling the alarm. On a Raspberry Pi the GUI can also be used to toggle screen brightness between high and low as well as turning it to sleep entirely. These buttons will be disabled if the system file `/sys/class/backlight/rpi_backlight/brightness` does not exist.

The second form generates an alarm based on the configuration file and plays it. This can be used as a CLI interface for the alarm. Use cron to manually schedule an alarm.

In either case, scheduling an alarm is done by adding a new cron entry to `alarm_builder.py`, either through the GUI or manually. **This means the alarm will play regardless of whether the GUI is running or not!** Also note that if enabled, the radio stream spawns a new `mplayer` process separate from the Python process running the alarm. The GUI's _Radio_ as well as _Close_ buttons take care of terminating this process when the radio is turned off, but in CLI mode you need to terminate the stream separately. This can be done with the included `stop.sh` shell script.

The optional argument in both forms is a path to a configuration file for customizing the alarm, see [config_readme.md](./config_readme.md) for instructions. By default `alarm.config` will be used.

Note that while the alarm time can be set from the GUI, the date cannot. The alarm is hard coded to occur every monday to friday at the specified time.


The interface to `alarm_builder.py` is:
```
positional arguments:
  config         path to the config file

optional arguments:
  -h, --help     show this help message and exit
```

The GUI also supports a fullscreen mode:
```
Run alarmpi GUI

positional arguments:
  config        path to an alarm configuration file. Defaults to alarm.config

optional arguments:
  -h, --help    show this help message and exit
  --fullscreen  launch the script in fullscreen mode
  --debug       launch in debug mode
```
