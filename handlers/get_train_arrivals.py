#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helper module for fetching the next 3 trains arriving at Espoo station using the
Finnish Transport agency's DigiTraffic API.
https://www.digitraffic.fi/en/railway-traffic/
https://www.digitraffic.fi/rautatieliikenne/#liikennepaikan-saapuvat-ja-l%C3%A4htev%C3%A4t-junat-lukum%C3%A4%C3%A4r%C3%A4rajoitus

This module differs from the other content handlers in that it is not a subclass
of apcontent.AlarmpiContent and not called by sound_the_alarm. Instead this serves
as a direct helper module to clock for fetching the next train arrivals.
"""

import requests
import datetime


def get_next_3_arrivals():
    """Get arrival time table rows of the next 3 commuter trains stopping at Espoo station."""
    response = fetch_daily_train_data()
    espoo = filter_espoo_trains(response)

    arrivals = [get_espoo_arrival_row(train) for train in espoo]
    # sort by either liveEstimateTime (if available) or arrival time
    for row in arrivals:
        if "liveEstimateTime" in row:
            sort_key = "liveEstimateTime"
        else:
            sort_key = "scheduledTime"
        row["timeToOrder"] = row[sort_key]

    arrivals.sort(key=lambda t: timestamp_to_datetime(t["timeToOrder"]))
    return arrivals[:3]


def fetch_daily_train_data():
    """API call to get the next 3 arriving at Espoo station."""
    url = "https://rata.digitraffic.fi/api/v1/live-trains/station/EPO"
    params = {
        "arrived_trains": 1,  # minumum value to already arrived and departed trains is 1
        "arriving_trains": 5,
        "departed_trains": 1
    }

    r = requests.get(url, params=params)
    return r.json()


def filter_espoo_trains(response):
    """Filter a list of API response trains to arriving commuter trains stopping at Espoo
    and heading towards Helsinki.
    Args:
        trains (list): list of API response trains
    Return:
        the list of filtered trains
    """
    filtered = [train for train in response if
                train["timetableType"] == "REGULAR" and
                train["trainCategory"] == "Commuter" and
                train["timeTableRows"][-1]["stationShortCode"] == "HKI" and
                "actualTime" not in train
                ]
    return filtered


def get_espoo_arrival_row(train):
    """Return the ARRIVAL row for Espoo from timeTableRows of an API response train.
    Args:
        train (dict): a single train object from an API response
    Return:
        the row matching Espoo arrival time as a dict
    """
    rows = [row for row in train["timeTableRows"] if row["type"]
            == "ARRIVAL" and row["stationShortCode"] == "EPO"]
    return rows[0]


def timestamp_to_datetime(s):
    """Convert a timestamp to a Python datetime.
    Args:
        s (str) a timestamp in %Y-%m-%dT%H:%M:%S.000Z
    Returns:
        a datetime.datetime instance
    """
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.000Z")
