#!/bin/python
# -*- coding: utf-8 -*-
import time
import datetime
import num2words

import apcontent


class Greeting(apcontent.AlarmpiContent):
    """Creates greeting messages based on current time of day."""

    def __init__(self, section_data):
        super().__init__(section_data)

    def build(self):
        today = datetime.datetime.today()
        day_of_month = num2words.num2words(today.day, ordinal=True)

        # current date and time as a spoken sentance,
        # eg. Wednesday August Twenty Second, 22:37
        current_date = "{}{}".format(time.strftime("%A %B "), day_of_month)
        current_time = time.strftime("%I:%M %p")  # eg. 6:36 pm

        if today.hour < 12:
            period = 'morning'
        elif today.hour >= 12:
            period = 'afternoon'
        elif today.hour >= 17:
            period = 'evening'

        greeting = "Good {}, {}. It's {}. The time is {}.\n\n".format(
            period,
            self.section_data["name"],
            current_date,
            current_time
        )

        self.content = greeting
