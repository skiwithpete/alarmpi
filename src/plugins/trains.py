from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer

from src.handlers import get_next_trains



class TrainPlugin:

    def __init__(self, parent):
        self.parent = parent
        self.parser = get_next_trains.TrainParser()

    def create_widgets(self):
        """Create and set QLabels for displaying train components."""
        self.train_labels = []
        for i in range(get_next_trains.MAX_NUMBER_OF_TRAINS):
            label = QLabel(self.parent.main_window)
            self.parent.main_window.left_grid.addWidget(label, i, 0)
            self.train_labels.append(label)

        self.parent.main_window.left_grid.setRowStretch(get_next_trains.MAX_NUMBER_OF_TRAINS, 1)

    def setup_train_polling(self):
        """Setup polling for next train departure."""
        self.update_trains()

        _5_MINUTES = 5*60*1000
        _timer = QTimer(self.parent.main_window)
        _timer.timeout.connect(self.update_trains)
        _timer.start(_5_MINUTES)

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
                    msg = "{} {} => {}".format(line_id, scheduled_time, estimate_time)

                else:
                    msg = "{} {}".format(line_id, scheduled_time)

                if train["cancelled"]:
                    msg = "{} {} CANCELLED".format(line_id, scheduled_time)

                label.setText(msg)

            # API response may contain fewer trains than MAX_NUMBER_OF_TRAINS trains,
            # clear any remaining labels.
            except IndexError:
                label.clear()
