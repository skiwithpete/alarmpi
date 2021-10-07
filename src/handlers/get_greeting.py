from datetime import datetime
import locale

import num2words

from src import apcontent


# Force the use of C locale for strftime calls
locale.setlocale(locale.LC_TIME, "C")

class Greeting(apcontent.AlarmpiContent):
    """Creates greeting messages based on current time of day."""

    def __init__(self, section_data, alarm_time_override):
        super().__init__(section_data)
        self.alarm_time_override = alarm_time_override

    def build(self):
        today = datetime.today()
        day_of_month = num2words.num2words(today.day, ordinal=True)
        current_weekday = today.strftime("%A")
        current_month = today.strftime("%B")

        # Convert 24 hour override format to 12 hour format
        if self.alarm_time_override:
            alarm_time = datetime.strptime(self.alarm_time_override, "%H:%M").strftime("%I:%M %p") # eg. 6:36 pm
        else:
            alarm_time = datetime.now().strftime("%I:%M %p")

        if today.hour < 12:
            period = "morning"
        elif today.hour >= 17:
            period = "evening"
        elif today.hour >= 12:
            period = "afternoon"

        greeting = "Good {period}, {name}. It's {weekday} {month} {day_of_month}. The time is {time}.\n\n".format(
            period=period,
            name=self.section_data["name"],
            weekday=current_weekday,
            month=current_month,
            day_of_month=day_of_month,
            time=alarm_time
        )

        self.content = greeting
