import logging

import board
import adafruit_dht


event_logger = logging.getLogger("eventLogger")
PIN = board.D4  # the GPIO pin the sensor is connected to


class DHT22Client:
    """Get readings from a DHT22 sensor."""

    def __init__(self):
        self.dht_device = adafruit_dht.DHT22(PIN, use_pulseio=False)

    def get_temperature(self):
        try:
            return self.dht_device.temperature
        except RuntimeError as e:
            event_logger.error(str(e))
        except Exception as e:
            event_logger.error("%s: %s", type(e).__name__, str(e))
            self.dht_device.exit()
