import logging

import board
import adafruit_dht

from src import apcontent


# Use pluginLogger to send (frequent) error events to separate file in order to keep
# main event log clean.
plugin_logger = logging.getLogger("pluginLogger")


class DHT22Client(apcontent.AlarmpiContent):
    """Get readings from a DHT22 sensor."""

    def __init__(self, section_data):
        super().__init__(section_data)
        PIN = board.pin.Pin(self.section_data["GPIO"])
        self.dht_device = adafruit_dht.DHT22(PIN, use_pulseio=False)
        self.error_counter = 0

    def try_get_temperature(self):
        """Attempt to read temperature from the sensor. As per Adafruit library documentation:
            Errors happen fairly often, DHT's are hard to read, just keep going.
            https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup
        Return None if call fails. Consecutive failed calls are logged as events.
        """
        ERROR_LIMIT = 3
        try:
            t = self.dht_device.temperature
            self.error_counter = 0
            return t
        except RuntimeError as e:
            self.error_counter += 1
            if self.error_counter >= ERROR_LIMIT:
                plugin_logger.error("Previous %s temperature reads failed. Latest received error: %s", ERROR_LIMIT, str(e))
                self.error_counter = 0

        # Log other exceptions as is
        except Exception as e:
            plugin_logger.error("%s: %s", type(e).__name__, str(e))
            self.error_counter += 1
