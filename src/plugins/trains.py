from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer

from src.handlers import get_next_trains


class TrainPlugin:

    def __init__(self, parent):
        self.parent = parent
        self.config_data = parent.config["plugins"]["HSL"]
        self.parser = get_next_trains.TrainParser(self.config_data)

    def create_widgets(self):
        """Create and set QLabels for displaying train components."""
        self.train_labels = []
        MAX_NUMBER_OF_TRAINS = self.config_data["trains"]

        for i in range(MAX_NUMBER_OF_TRAINS):
            label = QLabel(self.parent.main_window)
            self.parent.main_window.left_plugin_grid.addWidget(label)
            self.train_labels.append(label)

    def setup_polling(self):
        """Setup polling for next train departure."""
        self.update_trains()

        # Assume refresh interval in the config as seconds
        refresh_interval_msec = self.config_data["refresh_interval"] * 1000
        _timer = QTimer(self.parent.main_window)
        _timer.timeout.connect(self.update_trains)
        _timer.start(refresh_interval_msec)

    def update_trains(self):
        """Fetch new train data from DigiTraffic API and display on the right sidebar."""
        trains = self.parser.run()

        if trains is None:
            for label in self.train_labels:
                label.setText("ERR")
            return

        for i, label in enumerate(self.train_labels):
            try:
                train = trains[i]
                line_id = train["commuterLineID"]
                scheduled_time = train["scheduledTime"].strftime("%H:%M")

                # If an estimate exists, display both values
                if train["liveEstimateTime"]:
                    estimate_time = train["liveEstimateTime"].strftime("%H:%M")
                    msg = "{} {} ⇒ {}".format(line_id, scheduled_time, estimate_time)

                else:
                    msg = "{} {}".format(line_id, scheduled_time)

                if train["cancelled"]:
                    msg = "{} {} CANCELLED".format(line_id, scheduled_time)

                label.setText(msg)

            # API response may contain fewer trains than there are labels,
            # clear any remaining labels.
            except IndexError:
                label.clear()
