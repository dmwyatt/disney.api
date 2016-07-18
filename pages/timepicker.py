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

from helpers import roundTime, difference_in_minutes
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

	def select_time(self, desired_dt: datetime.datetime, leeway: int=None, round_to_closest=True):
		"""
		Selects a time from the time select.

		If `leeway` is not provided and `round_to_closest` is False, we try to select
		the exact time in `desired_dt`.

		If `round_to_closest` is True we ignore `leeway` and select the closest
		time to that specified in `desired_dt`.

		If `leeway` is provided and `round_to_closest` is False, we select the time
		closest to `desired_dt` that is less than `leeway` minutes away.


		:param desired_dt:
		:param leeway:
		:param round_to_closest:
		:return:
		:raises TimeNotBookableError: If provided arguments do not allow us to select anything.
		"""
		select_me = None
		if leeway is not None or round_to_closest:
			closest = None
			for selectable_value in self.selectable_values:
				selectable_value_dt = parser.parse(selectable_value)
				selectable_value_dt = selectable_value_dt.replace(year=desired_dt.year, month=desired_dt.month,
				                                                  day=desired_dt.day)
				if not closest:
					closest = selectable_value_dt
				closest_minutes_delta = difference_in_minutes(selectable_value_dt, closest)
				if not round_to_closest:
					if closest_minutes_delta < leeway:
						select_me = selectable_value
				else:
					select_me = selectable_value

		else:
			select_me = desired_dt.strftime('%H:%M')

		logger.info("Trying to select %s from %s", select_me, self.selectable_values)
		if select_me not in self.selectable_values:
			raise TimeNotBookableError("Cannot select '{}' from {}".format(select_me, self.selectable_values))

		self.select.select_by_value(select_me)

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


