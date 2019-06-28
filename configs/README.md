
## Alarm configuration
Alarm content can be configured by editing `alarmpi.config`.
The file specifies which components of the alarm are enabled and which text-to-speech (TTS) engine should be used, if any.

### alarm.config description

**[main]**  
  * **readaloud=0** disables TTS. The contents of the enabled sections will still be printed to stdout and a beeping sound effect will play as the alarm.
  * **nthost** determines a url to test for network connectivity. While many of the alarm components rely on API calls, an alarm should play even when the network is down. In this case a beeping sound effect will play.
  * **end** an ending greeting to be used by the TTS client after all components, apart from radio stream, have been processed.

**[alarm]**  
  * **include_weekends** By default the alarm only plays on weekdays. Enabling this features also runs the alarm on weekends. Note that the alarm date cannot be fine-tuned any further.
  * **nightmode_offset** determines nightmode. During nightmode the screen will automatically blank after a short while of touching the screen. Nightmode begins **nightmode_offset** hours before the alarm time.
    * Only takes effect on a Raspberry Pi

**[greeting], [openweathermap], [BBC_news]**  
  * These are the three main content sections determining actual content of the alarm.
  * `handler` points to a module in the `/handlers` directory responsible for creating the content.

   * **[openweathermap]** needs some additional configuration including an API key to openweathermap.org and a cityid for the city whose weather to forecast. See https://openweathermap.org/appid for registering for an API key and http://bulk.openweathermap.org/sample/ for cityid codes.
   * API key should be placed in a simple json file of
   ```
   {
     "key": API_KEY
   }
   ```
   The file should then be pointed to by the `key_file` option in the configuration.
   * Disabled by default

**Note:** content sections are parsed in the order they appear in the configuration. Therefore the greeting should come first.


#### TTS engines  
Three TTS engines are supported:  

**[google_gcp_tts]**  
Google Cloud Text-to-Speech engine. This provides the most human-like speech, but requires some additional setup. As this is a Google Cloud platform API, it requires a Google Cloud project with billing enabled.

Follow the quick start guide in https://cloud.google.com/text-to-speech/docs/quickstart-protocol to setup a project. After creating and downloading a service account key, specify the path to your key as the `key_file` option

While this is a paid API, there is a free tier of 1 million characters per month. This should easily cover the alarm's needs: a single run of the script generates about 1100 characters worth of text; running the script once per day therefore only generates a total of some 33 000 characters. See https://cloud.google.com/text-to-speech/pricing and https://cloud.google.com/text-to-speech/quotas for more information.
  * Disabled by default

**[google_translate_tts]**  
Google Translate Text-to-Speech engine. This uses an undocumented and unofficial API used in Google Translate. Has a limit of 200 characters per requests which results in noticeable pauses between chunks of text. Google may change or prevent using this API at any time.
  * This is the default enabled choice

**[festival_tts]**  
Festival is a general purpose TTS system. Does not require an internet access and provides by far the most robotic voice.


**Notes:**
 * If more than one TTS engine are enabled, the first one will be used.
 * If all TTS engines are disabled but **readaloud=1** is set, Festival will be used.
 * If TTS feature is diabled with **readaloud=0**, a beeping sound effect will be played as the alarm.

**[radio]**  
Determines the url to an online radio stream to play (if any). Uses the `mplayer` command line movie player to play the stream. The stream is played after all TTS content has been processed.

If enabled, the UI's _radio_ button can also be used to play the stream.
 * radio feature is disabled if no url is provided.

**Note:** The radio stream plays in a separate process from the Python process running the alarm. While the UI's _radio_ and _close_ buttons take care of terminating the process, a separate `stop.sh` shell script can also be used to terminate both processes. This is useful if the alarm is run in headless mode.

**[polling]**  
This enables the two polling features of the main window. When enabled
  1. weather data from openweathermap.org is displayed on the right side of the window. Updated every 30 minutes. Disabled if no keyfile is present in **[openweathermap]**, see above.
  2. the next departing trains from Espoo train station is shown on the left. Data is fetched from Finnish Transport agency's DigiTraffic API, see https://www.digitraffic.fi/en/railway-traffic/. This is largely a hardcoded feature to serve my own use case.
Both polling features are disabled by default.

### Using a custom configuration
You can either modify the provided configuration file `alarm.config` or create a new file and pass that to `alarm_builder.py` and `main.py` via a command line argument, eg.
```
python main.py my_config.config
```

### Extending the alarm with custom content
Extending the alarm with you're own content is simple:

 1. Create a handler for your new content and place it in the `/handlers` folder. It should subclass `apcontent.AlarmpiContent` and implement the `build` method. This function is where the magic happens: it should store whatever string content to pass to the alarm as the `content` attribute. A minimal handler implementation is something like:
 ```
 import apcontent

 class Handler(apcontent.AlarmpiContent):

    def build(self):
        self.content = "Text-to-Speech content goes here"
 ```

 See any of the existing handlers for reference. Note that when content is parsed, only the first class from each handler is read. Therefore, your handler should be a single class.

 2. Set the `handler` option in the configuration file to your new handler without the folder name.

 3. Set `type=content` and `enabled=1` in the configuration.

Adding a new TTS engine can be done similarly:

 1. Write the handler. It should should subclass `aptts.AlarmpiTTS` and implement the `play` method.

 2. Create a configuration section with `type=tts`

  * You can use the `key_file` option to set reference an API access token file to the constructor if required. This will be passed to the initializer.