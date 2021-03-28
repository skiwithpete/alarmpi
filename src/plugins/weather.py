from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

from src.handlers import get_open_weather



class WeatherPlugin:

    def __init__(self, parent):
        self.parent = parent
        config = parent.env.get_section("openweathermap")
        self.parser = get_open_weather.OpenWeatherMapClient(config)

    def create_widgets(self):
        """Create and set QLabels for displaying weather components."""
        self.temperature_label = QLabel(self.parent.main_window)
        self.wind_label = QLabel(self.parent.main_window)
        self.icon_label = QLabel(self.parent.main_window)

        # Set the labels to the first 3 rows and a larger strecth factor to the last row
        # to pull them closer together
        self.parent.main_window.right_grid.addWidget(self.temperature_label, 0, 0, Qt.AlignRight)
        self.parent.main_window.right_grid.addWidget(self.wind_label, 1, 0, Qt.AlignRight)
        self.parent.main_window.right_grid.addWidget(self.icon_label, 2, 0, Qt.AlignRight | Qt.AlignTop)
        self.parent.main_window.right_grid.setRowStretch(2, 1)

    def setup_weather_polling(self):
        """Setup polling for updating the weather every 30 minutes."""
        self.update_weather()

        _30_MINUTES = 30*60*1000
        _timer = QTimer(self.parent.main_window)
        _timer.timeout.connect(self.update_weather)
        _timer.start(_30_MINUTES)

    def update_weather(self):
        """Update the weather labels on the main window. Makes an API request to
        openweathermap.org for current temperature and windspeed.
        """
        weather = self.parser.fetch_and_format_weather()

        if weather is None:
            self.temperature_label.setText("ERR")
            self.wind_label.setText("ERR")
            return

        temperature = weather["temp"]
        wind = weather["wind_speed_ms"]

        msg = "{}°C".format(round(temperature))
        self.temperature_label.setText(msg)

        msg = "{}m/s".format(round(wind))
        self.wind_label.setText(msg)

        icon_id = weather["icon"]
        icon_binary = get_open_weather.OpenWeatherMapClient.get_weather_icon(icon_id)

        pixmap = QPixmap()
        pixmap.loadFromData(icon_binary)
        self.icon_label.setPixmap(pixmap)