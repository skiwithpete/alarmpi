
## Alarm configuration
Alarm content can be configured by editing `alarmpi.config`.
The file specifies which components of the alarm are enabled and which text-to-speech (TTS) engine should be used, if any.

### alarm.config description

**[main]**  
  * **readaloud=0** disables TTS. The contents of the enabled sections will still be printed to stdout and a beeping sound effect will play as the alarm.
  * **nthost** determines a url to test for network connectivity. While many of the alarm components rely on API calls, an alarm should play even when the network is down. In this case a beeping sound effect will play.
  * **end** an ending greeting to be used by the TTS client after all components, apart from radio stream, have been processed.

**[greeting], [yahoo_weather], [BBC_news]**  
  * These are the three main content sections determining actual content of the alarm.
  * recognized as content by `type=content`
  * `handler` points to a module in the `/handlers` directory responsible for creating the content.

   * **[yahoo_weather]** needs some additional parameters including a WOEID code of the forecast target region, and flags for including additional wind effects to the forecast. See
   http://woeid.rosselliot.co.nz/ for WOEID codes.  


**Note:** content sections are parsed in the order they appear in the configuration. Therefore the greeting should come first.


#### TTS engines  
Three TTS engines are supported:  

**[google_gcp_tts]**  
Google Cloud Text-to-Speech engine. This provides the most human-like speech, but requires some additional setup. Since this is a Google Cloud platform API, you need to setup a Google Cloud project and enable billing.

Follow the quick start guide in https://cloud.google.com/text-to-speech/docs/quickstart-protocol to setup a project. After creating and downloading a service account key, specify the path to your key as the `key_file` option

While this is a paid API, there is a free tier of 1 million characters per month. This should easily cover the alarm's needs: a single run of the script generates about 1100 characters worth of text; running the script once per day therefore only generates a total of some 33 000 characters. See https://cloud.google.com/text-to-speech/pricing and https://cloud.google.com/text-to-speech/quotas for more information.

**[google_translate_tts]**  
Google Translate Text-to-Speech engine. This uses an undocumented and unofficial API used in Google Translate. Has a limit of 200 characters per requests which results in noticeable pauses between chunks of text. Google may change or prevent using this API at any time. This is the enabled choice by default.

**[festival_tts]**  
Festival is a general purpose TTS system. Does not require an internet access and provides by far the most robotic voice.


**Notes:**
 * If more than one TTS engine are enabled, the first will be used.
 * If all TTS engines are disabled but **readaloud=1** is set, Festival will be used.
 * If **readaloud** is disabled, a beeping sound effect will be played.

**[radio]**  
Determines the url to the radio stream. Uses the `mplayer` command line movie player to play the stream. The stream is played after all TTS content has been processed and is diabled if no url is provided.

**Note:** If the radio is enabled and the alarm is run via cron, the stream has to be stopped by terminating the `mplayer` process. Use the provided `stop.sh` script to kill the alarm (and the stream).

### Using a custom configuration
You can either modify the provided configuration file `alarm.config` or create a new file and pass that to `sound_the_alarm.py` and `main.py` via a command line argument. To re-create the original configuration file, use the `--init-config` switch.

### Extending the alarm with custom content
Extending the alarm with you're own content is simple:

 1. Create a handler for your new content and place it in the `/handlers` folder. It should subclass `apcontent.AlarmpiContent` and implement the `build` method. This function is where the magic happens: it should store whatever string content to pass to the alarm as the `content` attribute. A minimal handler implementation is something like:
 ```
 import apcontent

 class Handler(apcontent.AlarmpiContent):

    def build(self):
        self.content = "Text-to-Speech content goes here"
 ```

 See any of the existing handlers for reference. Note that `sound_the_alarm.py` tries to import the first class (in alphabetical order) from each handler. Therefore, your handler should be a single class.

 2. Set the `handler` option in the configuration file to your new handler without the folder name.

 3. Set `type=content` and `enabled=1` in the configuration.

Adding a new TTS engine can be done similarly:

 1. Write the handler. It should should subclass `aptts.AlarmpiTTS` and implement the `play` method.

 2. Create a configuration section with `type=tts`

  * You can use the `key_file` option to set reference an API access token file to the constructor if required. This will be passed to the initializer.
