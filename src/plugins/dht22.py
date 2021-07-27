from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer, Qt

from src.handlers import get_dht22_readings


class DHT22Plugin:

    def __init__(self, parent):
        self.parent = parent
        self.config_data = parent.config["plugins"]["DHT22"]
        self.client = get_dht22_readings.DHT22Client(self.config_data)

    def create_widgets(self):
        """Create and set QLabel for displaying temperature."""
        self.dht22_label = QLabel(self.parent.main_window)
        self.parent.main_window.right_grid.addWidget(self.dht22_label, 3, 0, Qt.AlignRight | Qt.AlignTop)

    def setup_polling(self):
        self.update_temperature()

        refresh_interval_msec = self.config_data["refresh_interval"] * 1000
        _timer = QTimer(self.parent.main_window)
        _timer.timeout.connect(self.update_temperature)
        _timer.start(refresh_interval_msec)

    def update_temperature(self):
        """Fetch new temperature readings from the handler."""
        temperature = self.client.try_get_temperature()

        # Only change the label if a valid temperature was received
        if temperature:
            msg = "⌂ {}°C".format(round(temperature))
            self.dht22_label.setText(msg)
