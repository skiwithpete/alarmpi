# Alarmpi

A clock radio for a Raspberry Pi with customizable alarm.
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


This is a fork of skiwithpete's alarmpi project: https://github.com/skiwithpete/alarmpi. After seeing it on [YouTube](https://youtu.be/julETnOLkaU), I thought it was awsome and knew I wanted to use it to replace my old night table clock radio.


### Main Features
 * A greeting based on time of day
 * Tells the day's weather using Yahoo Weather
 * Reads latest news from BBC World RSS feed
 * Stream a radio station using `mplayer`
 * A GUI for displaying current time and setting the alarm

The first 3 largely corresponds to the features in the original project. The latter two I build for to match my own use cases.

The GUI for the clock is rather primitive due to hardware limitations: I build this project to run on a Raspberry Pi together with the official touch screen display with no additional input device. Since Raspbian is not a touch screen OS, it's support is limited to emulating mouse clicks. The alarm is therefore set using a binary based system for the hour and minute.

![Main window](resources/clock_main.png)
![schedule window](resources/clock_schedule.png)



I've made a number of changed to the original project:
 * Ported to Python 3 (Python 2 is unsupported)
 * Changed naming conventions to be more PEP 8 compliant with other minor cleanups
 * Added a GUI for a clock
 * Added option to stream radio
 * Removed some modules I deemed unnecessary (mainly due to removed features, see the next point)
 * Removed features not applicable to my use case (including turning lights on and off, playing songs and reading stocks from Yahoo Finance, which has been discontinued)
 * Reorganized the file structure
 * Changed which text-to-speech engines are available, see below
 * Changed audio processing to use in-memory objects, thus removing the need to setup a ramdrive
 * Added unit tests



### Setup
 1. First, install required system packages with

  ```apt install ffmpeg festival mplayer portaudio19-dev python-all-dev```

  This includes the Festival text-to-speech engine, the command line movie player mplayer and audio libraries enabling playback of mp3 files directly in Python.

 2. Next, install required Python packages:

  ```pip install -r requirements.txt```

  A virtualenv is recommended.

 3. If you haven't done so already, initialize a new crontab with

 ```crontab -e```

  and follow the instructions.

   * If a crontab already exists, you may want to create a backup with `crontab -l > cron.backup`. It can be restored with `crontab cron.backup`.

 4. Optionally, run unit tests with

  ```python -m unittest -v tests/test_*.py```


### Usage
If you have display attached to your Pi, run the script with

```python main.py```

This opens the GUI for displaying current time and scheduling the alarm. The scheduling is done by adding a new cron entry to `sound_the_alarm.py`. **This means the alarm will play regardless of whether the GUI is running or not!**. While the time of the alarm can be set from the GUI, the date cannot. The alarm is hard coded to occur every monday to friday at the specified time. Of course, you can change it by editing crontab manually.

In a headless environment running `main.py` will fail since Tkinter cannot be imported. Instead run the alarm directly with

```python sound_the_alarm.py <path-to-configuration-file>```

This parses the configuration file (by default `alarm.config`), creates a corresponding alarm and runs it. Use cron to schedule the alarm manually.

The interface to `sound_the_alarm.py` is:
```
positional arguments:
  config         path to the config file

optional arguments:
  -h, --help     show this help message and exit
  --init-config  re-create the default configuration file alarm.config.
                 Overwrites existing file.
```

#### alarm.config description
The configuration file specifies which components of the alarm are enabled and which text-to-speech (TTS) engine should be used (if any).

**[main]**  
  * `readaloud=0` disables TTS. The contents of the enabled sections will still be printed to stdout and a beeping alarm will play.
  * `nthost` determines which url should be tested for network connectivity. If the network connection is detected to be down a beeping sound effect is played instead of performing any API requests (ie. only the beeping alarm is played).
  * `end` an ending greeting to be used by the TTS client

**content**  
  * section with `type=content` determine the actual content (apart from the radio stream) of the alarm. Handlers point to files in the `/handlers` directory responsible for creating the content.
  * `[yahoo_weather]` specify your own region's WOEID code for weather predictions. See http://woeid.rosselliot.co.nz/. You can also enable extra wind related processing (with some conditions: wind chill is only reported for windy enough winter months)

  **A note on content preference**  
  Content sections are parsed in the order they appear in the configuration. The greeting should come first.


**tts engines**  
Three for TTS engines are supported:
 1. `[google_gcp_tts]` Google Cloud Text-to-Speech engine. This provides the most human-like speech, but requires some additional setup. Since this is a Google Cloud platform API, you need to setup a Google Cloud project and enable billing.

    Follow the quick start guide in https://cloud.google.com/text-to-speech/docs/quickstart-protocol to setup a project. After creating and downloading a service account key, instead of setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable, specify the path to your key as the `private_key_file` option in the configuration file.

    While this is a paid API, there is a free tier of 1 million characters per month. This should easily cover the alarm's needs: a single run of the script generates about 1100 characters worth of text; running the script once per day therefore only generates a total of some 33 000 characters. See https://cloud.google.com/text-to-speech/pricing and https://cloud.google.com/text-to-speech/quotas for more information.

 2. `[google_translate_tts]` Google Translate Text-to-Speech engine. This uses an undocumented and unofficial API used in Google Translate. Has a limit of 200 characters per requests which results in noticeable pauses between chunks of text. Google may prevent using this API at any time. This is the enabled choice by default.

 3. `[festival_tts]` Festival is a general purpose externally installed TTS system. Does not require an internet access and provides by far the most robotic voice.

 **A note on TTS preference**  
  The first TTS engine is used even if several are enabled. If all TTS engines are disabled but `readaloud=1` is set, Festival will be used.

  If `readaloud` is disabled, a beeping sound effect will be played.

**[radio]**  
Determines the url to the radio stream. Uses `mplayer` system package. The stream is payed after all TTS content has been processed. The `timeout` option can be used to specify a time in seconds after the stream should close. This is handy when the script is run from cron, in which case the script cannot be keyboard interrupted.

 **Note**  
 If the radio is enabled and the alarm is run via cron, the stream cannot be keyboard interrupted via `Ctr-c` and will play indefinitely by default. Either use the provided `stop.sh` script to kill the alarm (and the stream) or consider setting a `timeout`.

#### Using a custom configuration
You can either modify the provided configuration file `alarm.config` or create a new file and pass that to `sound_the_alarm.py` via the `config` argument. To re-create the original configuration file, use the `--init-config` switch.

#### Extending alarm.config with more content
Extending the alarm with more content is simple:

 1. Create a handler for your new content and place it in the `/handlers` folder. It should subclass `apcontent.AlarmpiContent` and implement the `build` method. This function is where the magic happens: it should store whatever string content to pass to the alarm as the `content` attribute. A minimal handler implementation is something like:
 ```
 import apcontent

 class Handler(apcontent.AlarmpiContent):

     def build(self):
         self.content = "Text-to-Speech content goes here"
```
See any of the existing handlers for reference.

 2. Register your handler in `sound_the_alarm.py`:
 ```
 handler_map = {
     "get_gcp_tts": "GoogleCloudTTS",
     "get_google_translate_tts": "GoogleTranslateTTSManager",
     "get_festival_tts": "FestivalTTSManager",
     "get_greeting": "Greeting",
     "get_bbc_news": "NewsParser",
     "get_yahoo_weather": "YahooWeatherClient",
     "my_new_module": "my_new_class"
 }
 ```

 2. Set the `handler` option in the configuration file to your new handler without the folder name.

 3. Set `type=content` and `enabled=1` in the configuration.

Adding a new TTS engine can be done simialrly:

 1. Write the handler. It should should subclass `aptts.AlarmpiTTS` and implement the `play` method.

 2. Create a configuration section with `type=tts`

  * You can use the `private_key_file` option to set reference an API access token file to the constructor if required. This will be then passed to the initializer.


Extending beyond these requires writing new processing logic in `sound_the_alarm.py`.
