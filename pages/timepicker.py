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


class TimePicker:
	select_toggle_selector = 'div.select-toggle[aria-owns="diningAvailabilityForm-searchTime-dropdown-list"]'
	list_wrapper_selector = 'span#searchTime-wrapper>div.listWrapper'
	list_selector = 'ol#diningAvailabilityForm-searchTime-dropdown-list'
	list_items_selector = '{}>li.selectOption'.format(list_selector)
	header_selector = '#checkAvailability'

	def __init__(self, browser: webdriver.PhantomJS):
		self.browser = browser

		self._cached_time_data = None

	@property
	def _time_ids(self):
		if self._cached_time_data is None:
			self._cached_time_data = {}
			self.displayed = True
			selections = self.browser.find_elements_by_css_selector(self.list_items_selector)
			for li in selections:
				value = li.get_attribute('data-value')
				li_id = li.get_attribute('id')

				# a time like 14:30
				if re.match('\d\d:\d\d', value):
					key = value
				# a period like 'breakfast' (represented by string of digits)
				elif re.match('\d+', value):
					key = li.get_attribute('data-display')
				else:
					assert False, "Invalid value: {}".format(value)

				self._cached_time_data[key] = li_id

		return self._cached_time_data


	@property
	def aria_hidden_value(self):
		try:
			return self.browser.find_element_by_css_selector(self.list_wrapper_selector).get_attribute('aria-hidden')
		except:
			with open('source.html', 'w') as f:
				f.write(self.browser.page_source)
				webbrowser.open('file://{}'.format(os.path.realpath('./source.html')))
			raise


	@property
	def aria_is_hidden(self):
		return self.aria_hidden_value != 'false'

	@property
	def displayed(self):
		return not self.aria_is_hidden and self.browser.find_element_by_css_selector(self.list_wrapper_selector).is_displayed()

	@displayed.setter
	def displayed(self, b: bool):
		if b and self.displayed:
			return
		elif b and not self.displayed:
			self.toggle()
		elif not b and self.displayed:
			self.toggle()
		elif not b and not self.displayed:
			return

	def get_id_for_dt(self, dt: datetime.datetime=None, breakfast: bool=None, lunch: bool=None, dinner: bool=None) -> str:
		if dt:
			time = roundTime(dt, 1800).strftime('%H:%M')
			return self._time_ids[time]
		else:
			assert breakfast or lunch or dinner, "If not providing datetime, you must specify breakfast, lunch or dinner."
			meal = 'breakfast'
			if lunch:
				meal = 'lunch'
			elif dinner:
				meal = 'dinner'
			return self._time_ids[meal]

	def select_time(self, dt: datetime.datetime):
		assert self.is_selectable_time(dt)
		time_id = self.get_id_for_dt(dt)
		self._select_option(time_id)

	def select_breakfast(self):
		self._select_option(self._time_ids['breakfast'])

	def select_lunch(self):
		self._select_option(self._time_ids['lunch'])

	def select_dinner(self):
		self._select_option(self._time_ids['dinner'])

	def _select_option(self, select_id):
		assert select_id in self._time_ids.values()

		self.displayed = True
		self.browser.find_element_by_id(select_id).click()

	@property
	def earliest(self) -> str:
		return self.selectable_times[0]

	@property
	def latest(self) -> str:
		return self.selectable_times[-1]

	@property
	def selectable_times(self) -> str:
		times = list(self._time_ids.keys())
		nope = ['lunch', 'dinner', 'breakfast']
		times = [x for x in times if x not in nope]
		times.sort()
		return times

	def is_selectable_time(self, dt) -> bool:
		dt = roundTime(dt, 1800)
		times = [datetime.datetime.strptime(x, '%H:%M').replace(year=dt.year, month=dt.month) for x in self.selectable_times]
		times = []
		for x in self.selectable_times:
			times.append(datetime.datetime.strptime(x, '%H:%M')
			             .replace(year=dt.year, month=dt.month, day=dt.day))
		times.sort()
		return dt >= times[0] and dt <= times[-1]

	def toggle(self):
		if self.displayed:
			# Something in the way when list is displayed, so just click somewhere else
			self.browser.find_element_by_css_selector(self.header_selector).click()
			wait_for(lambda: not self.displayed, 2)
		else:
			clickme = self.browser.find_element_by_css_selector(self.select_toggle_selector)

			def clickable():
				try:
					clickme.click()
				except WebDriverException:
					return False
				return True

			wait_for(clickable, 2)
			wait_for(lambda: self.displayed, 2)

