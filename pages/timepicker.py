import datetime
import logging
import os
import time

import re
import webbrowser

from dateutil import parser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.support.select import Select

from helpers import roundTime, difference_in_minutes, format_dt
from pages.helpers import wait_for

logger = logging.getLogger(__name__)

class TimeNotBookableError(Exception):
	pass

class BasicTimePicker:
	select_selector = 'select#diningAvailabilityForm-searchTime'

	def __init__(self, browser: webdriver.PhantomJS):
		self.browser = browser

	@property
	def select_element(self):
		return self.browser.find_element_by_css_selector(self.select_selector)

	@property
	def select(self):
		return Select(self.select_element)

	@property
	def option_elements(self):
		return self.select_element.find_elements_by_tag_name('option')

	@property
	def selectable_values(self):
		return [x.get_attribute('value') for x in self.option_elements]

	@property
	def selectable_texts(self):
		return [x.text for x in self.option_elements]

	def select_exact_time(self, desired_dt: datetime.datetime):
		the_time = desired_dt.strftime('%H:%M')
		if not the_time in self.selectable_values:
			raise TimeNotBookableError("Cannot select '{}' from {}".format(the_time, self.selectable_values))
		self.select.select_by_value(the_time)

	def select_time_with_leeway(self, desired_dt: datetime.datetime, leeway: int):
		closest = None
		closest_delta = None
		for sv in self.selectable_values:
			if not re.match('\d\d:\d\d', sv):
				continue

			sv_dt = time_to_datetime(sv, desired_dt)

			if not closest:
				closest = sv_dt
				closest_delta = difference_in_minutes(desired_dt, closest)

			curr_sv_delta = difference_in_minutes(sv_dt, desired_dt)
			if curr_sv_delta < closest_delta:
				closest = sv_dt
				closest_delta = curr_sv_delta

		if closest_delta <= leeway:
			self.select_exact_time(closest)
		else:
			raise TimeNotBookableError("There is no selectable time that's "
			                           "less than {} minutes from {} "
			                           "in {}".format(leeway, format_dt(desired_dt), self.selectable_values))

	def select_closest_time(self, desired_dt: datetime.datetime):
		closest = None
		closest_delta = None
		for sv in self.selectable_values:
			if not re.match('\d\d:\d\d', sv):
				continue

			sv_dt = time_to_datetime(sv, desired_dt)

			if not closest:
				closest = sv_dt
				closest_delta = difference_in_minutes(desired_dt, closest)

			curr_sv_delta = difference_in_minutes(sv_dt, desired_dt)
			if curr_sv_delta < closest_delta:
				closest = sv_dt
				closest_delta = curr_sv_delta

		self.select_exact_time(closest)

	def select_meal(self, meal):
		try:
			self.select.select_by_visible_text(meal)
		except NoSuchElementException:
			raise TimeNotBookableError("Cannot select '{}' from {}".format(meal, self.selectable_texts))

	def select_breakfast(self):
		self.select_meal('Breakfast')

	def select_lunch(self):
		self.select_meal('Lunch')

	def select_dinner(self):
		self.select_meal('Dinner')


def time_to_datetime(the_time: str, reference_dt: datetime.datetime) -> datetime.datetime:
	"""
	Takes a string representing a time and a datetime.datetime that represents the day that time
	is on, and returns a datetime.datetime on that day with the new time.
	"""
	dt = parser.parse(the_time)
	return dt.replace(year=reference_dt.year, month=reference_dt.month, day=reference_dt.day)
