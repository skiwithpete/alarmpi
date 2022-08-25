# Client for fetching arriving commuter trains to a station using
# Finnish Transport agency's DigiTraffic API.
# https://www.digitraffic.fi/en/railway-traffic/
# https://www.digitraffic.fi/rautatieliikenne/#liikennepaikan-saapuvat-ja-l%C3%A4htev%C3%A4t-junat-lukum%C3%A4%C3%A4r%C3%A4rajoitus

import datetime
import logging

import requests
from dateutil import tz

from src import apcontent


event_logger = logging.getLogger("eventLogger")


# While this feature is not part of the alarm, subclassing AlarmpiContent provides
# access to the config.
class TrainParser(apcontent.AlarmpiContent):

    def run(self):
        """Run the parser: fetch and format a list of next departures. Return
        None if API call fails.
        """
        api_response = self.fetch_daily_train_data()
        if "error" in api_response:
            return api_response

        return self.format_next_departures(api_response)

    def format_next_departures(self, api_response):
        """Format a list of API response departures to a list of dicts
        to pass back to clock.py.
        """
        locals_ = self.filter_commuter_trains(api_response)

        departure_rows = []
        for train in locals_:
            row = self.get_local_departure_row(train)

            # Ignore already departed trains
            if "actualTime" in row:
                continue

            # Determine the timestamp key to be used for sorting:
            # if an estimate exists, use it, otherwise use scheduled departure time
            sort_key = "scheduledTime"
            scheduled_time_dt = self.utc_timestamp_to_local_datetime(row["scheduledTime"])
            live_estimate_time_dt = None
            if "liveEstimateTime" in row:
                # Check that liveEstimateTime differs from scheduledTime by at least 1 minute
                live_estimate_time_dt = self.utc_timestamp_to_local_datetime(
                    row["liveEstimateTime"])
                td = live_estimate_time_dt - scheduled_time_dt
                sort_key = "liveEstimateTime"

                if abs(td.seconds) < 60:
                    live_estimate_time_dt = None

            sort_dt = self.utc_timestamp_to_local_datetime(row[sort_key])
            departure_rows.append({
                "liveEstimateTime": live_estimate_time_dt,
                "scheduledTime": scheduled_time_dt,
                "commuterLineID": train["commuterLineID"],
                "cancelled": train["cancelled"],
                "sortKey": sort_dt
            })

        departure_rows.sort(key=lambda row: row["sortKey"])

        # Limit trains to return to the count in the config
        MAX_NUMBER_OF_TRAINS = self.section_data["trains"]
        return departure_rows[:MAX_NUMBER_OF_TRAINS]

    def fetch_daily_train_data(self):
        """API call to get the next local arrivivals."""
        URL = "https://rata.digitraffic.fi/api/v1/live-trains/station/{}".format(self.section_data["station_code"])
        params = {
            "arrived_trains": 1,  # API minimum
            "arriving_trains": 20,
            "departed_trains": 1
        }

        # Catch any network related errors from the request itself
        try:
            r = requests.get(URL, params=params)
        except Exception as e:
            event_logger.error(str(e))
            return {"error": {"message": str(e), "status_code": 503}}

        # Catch errors from succesfully sent requests
        if r.status_code != 200:
            return {"error": {"message": r.text, "status_code": r.status_code}}

        return r.json()

    def filter_commuter_trains(self, response):
        """Filter a list of API response trains to commuter trains heading towards Helsinki.
        Args:
            trains (list): list of API response trains
        Return:
            list of filtered trains
        """
        filtered = [train for train in response if
                    train["timetableType"] == "REGULAR" and
                    train["trainCategory"] == "Commuter" and
                    train["timeTableRows"][-1]["stationShortCode"] == "HKI"
                    ]

        return filtered

    def get_local_departure_row(self, train):
        """Given an API response train, return the DEPARTURE row of its timeTableRows
        Args:
            train (dict): a single train object from an API response
        Return:
            the local departure row of the train's timeTableRows
        """
        rows = [row for row in train["timeTableRows"] if
                row["type"] == "DEPARTURE" and
                row["stationShortCode"] == self.section_data["station_code"]
                ]

        return rows[0]

    def timestamp_to_datetime(self, s):
        """Convert a timestamp to a Python datetime.
        Args:
            s (str) a timestamp in %Y-%m-%dT%H:%M:%S.000Z
        Returns:
            a datetime.datetime instance
        """
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.000Z")

    def utc_timestamp_to_local_datetime(self, s):
        """Convert a timestamp str in UTC as returned by the API to a datetime
        in local timezone.
        Args:
            s (str) a timestamp in %Y-%m-%dT%H:%M:%S.000Z
        Returns:
            a datetime.datetime instance
        """
        tz_utc = tz.tzutc()
        tz_local = tz.tzlocal()

        utc = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.000Z")

        # Tell the datetime object that it's in UTC time zone since
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=tz_utc)

        return utc.astimezone(tz_local)

    def msecs_until_datetime(self, d):
        """Compute the number of milliseconds until input datetime. Input is
        assumed to be a local, future timestamp as a timezone aware datetime instance.
        """
        tz_local = tz.tzlocal()
        now = datetime.datetime.now(tz=tz_local)

        if d <= now:
            return 0

        return (d - now).seconds * 1000
