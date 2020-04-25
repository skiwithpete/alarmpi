#!/bin/python
# -*- coding: utf-8 -*-
import time
import datetime
import calendar

import num2words

from src import apcontent


class Greeting(apcontent.AlarmpiContent):
    """Creates greeting messages based on current time of day."""

    def __init__(self, section_data):
        super().__init__(section_data)

    def build(self):
        today = datetime.datetime.today()

        # Use the 'C' locale for generating weekday and month names
        with calendar.different_locale("C"):
            current_weekday = calendar.day_name[today.weekday()]
            current_month = calendar.month_name[today.month]

        day_of_month = num2words.num2words(today.day, ordinal=True)
        current_time = time.strftime("%I:%M %p")  # eg. 6:36 pm

        if today.hour < 12:
            period = 'morning'
        elif today.hour >= 17:
            period = 'evening'
        elif today.hour >= 12:
            period = 'afternoon'

        greeting = "Good {period}, {name}. It's {weekday} {month} {day_of_month}. The time is {time}.\n\n".format(
            period=period,
            name=self.section_data["name"],
            weekday=current_weekday,
            month=current_month,
            day_of_month=day_of_month,
            time=current_time
        )

        self.content = greeting
