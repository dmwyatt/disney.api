import json
import logging
from pathlib import Path
from pprint import pformat
from typing import Mapping, Union, Sequence

import arrow
import datetime
from dateutil import parser

from helpers import sort_datetimes_by_closeness_to_datetime, filter_datetimes
from pages.restaurant import RestaurantPageAvailabilityForm


logger = logging.getLogger(__name__)


class ConfigError(Exception):
	pass


class RestaurantsConfigEntry:
	"""
	Example entry with all options provided:

	{
		# Restaurant page url
	    "url": "https://disneyworld.disney.go.com/dining/magic-kingdom/cinderella-royal-table/",

	    # Datetime to find available reservations times for.
	    "datetime": "09/08/2016 18:00",

	    # Number of people in your party.
	    "party_size": 4,


	    # The following are optional.

	    # If you want to find all available reservations between two dates, you
	    # may optionally provide this option.  Note that we will check each day between
	    # the two dates, but we will only check the time from the 'datetime' on each day.
	    # Any time provided in 'to_date' is ignored.
	    "to_date":  "09/10/2016",

	    # If you provide "breakfast", "lunch" or "dinner" we will find times during those periods.
	    "period": "dinner",

	    # The number of minutes plus/minus you're willing to accept for a reservation.
	    # If not provided, we just use whatever Disney sends us when we tell them we want a time.
	    "leeway": 30
    }
	"""
	def __init__(self, data: Mapping[str, Union[str, int]]):
		self._data = data

		# required options
		self.url = data.get('url')
		assert self.url, "No 'url' field provided in:" + self._formatted_data()

		self.dt = data.get('datetime')
		assert self.dt, "No 'datetime' field provided in:" + self._formatted_data()
		self.dt = parser.parse(self.dt)

		self.party_size = data.get('party_size')
		assert self.party_size, "No 'party_size' field provided in:" + self._formatted_data()

		# optional
		self.period = self._validate_period()
		self.to_date = self._validate_to_date()

		self.to_date = data.get('to_date') if not data.get('to_date') else parser.parse(data.get('to_date'))

		self.leeway = data.get('leeway')

		self._cached_avail_form = None

	def _validate_to_date(self):
		to_date = self._data.get('to_date')
		if to_date:
			try:
				to_date = parser.parse(to_date)
			except ValueError:
				raise ConfigError("Cannot parse 'to_date' value: {}".format(to_date))
			return to_date.replace(hour=self.dt.hour, minute=self.dt.minute)

	def _validate_period(self):
		valids = ['breakfast', 'lunch', 'dinner']

		period = self._data.get('period')
		if period:
			assert period in valids, "'{}' is not a valid period.  Choose one of " + str(valids)

		self.breakfast = True if period == 'breakfast' else False
		self.lunch = True if period == 'lunch' else False
		self.dinner = True if period == 'dinner' else False

		return period

	def _formatted_data(self):
		return "\n{}".format(pformat(self._data))

	@property
	def availability_form(self):
		if self._cached_avail_form is None:
			self._cached_avail_form = RestaurantPageAvailabilityForm(self.url, implicit_wait=2)
		if not self._cached_avail_form.has_fetched:
			self._cached_avail_form.get()
		return self._cached_avail_form

	def get_availability(self):
		if self.to_date:
			logger.info("Checking availability for {the_time} at {name} on dates "
			            "between {start} - {end}, inclusive.".format(name=self.availability_form.name,
			                                                         the_time=self.dt.strftime("%H:%M"),
			                                                         start=self.dt,
			                                                         end=self.to_date))
		else:
			logger.info("Checking availability for {the_time} at "
			            "{name} on {date}.".format(the_time=self.dt.strftime("%H:%M"),
			                                       name=self.availability_form.name,
			                                       date=self.dt))

		get_avail = lambda x: self.availability_form.find_availability_for(
			x,
			self.party_size,
			breakfast=self.breakfast,
			lunch=self.lunch,
			dinner=self.dinner
		)

		return [get_avail(dt) for dt in self.datetimes]


	def get_times(self):
		availabilities = self.get_availability()

		joined_availabilities = []
		for a in availabilities:
			joined_availabilities.extend(a['available_times'])

		datetimes = sort_datetimes_by_closeness_to_datetime(joined_availabilities, self.dt)

		if self.leeway:
			datetimes = filter_datetimes(datetimes, self.leeway, self.dt)
		return datetimes

	@property
	def datetimes(self):
		if self.to_date:
			return arrow.Arrow.range('day', self.dt, self.to_date)
		return [self.dt]

	@classmethod
	def validate_json_file(cls, filepath: str) -> Sequence['RestaurantsConfigEntry']:
		p = Path(filepath)
		assert p.is_file(), "'{}' does not exist.".format(filepath)

		with p.open('r') as f:
			data = json.loads(f.read())


		return [RestaurantsConfigEntry(entry) for entry in data]

	@classmethod
	def get_many_from_json(cls, filepath: str) -> Sequence['RestaurantsConfigEntry']:
		return cls.validate_json_file(filepath)