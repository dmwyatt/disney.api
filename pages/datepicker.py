import datetime
from typing import Union, Sequence

from dateutil import parser
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from pages.helpers import wait_for, elem_has_class


class InvalidDate(Exception):
	pass

class DatePickerError(Exception):
	pass

class JqueryUIDatePicker:
	datepicker_selector = 'div.ui-datepicker'
	month_selector = 'span.ui-datepicker-month'
	year_selector = 'span.ui-datepicker-year'
	day_selector = 'td.ui-datepicker-current-day'
	selectable_days_selector = 'td[data-handler="selectDay"]'
	date_input_id = 'diningAvailabilityForm-searchDate'

	def __init__(self, browser: webdriver.PhantomJS, click_to_display_id: str):
		self._browser = browser
		self.click_to_display_id = click_to_display_id
		self.click_to_display_element = browser.find_element_by_id(click_to_display_id)

	def select_day(self, dt: datetime.date):
		self.go_to_date(dt)

		elems = self._picker.find_elements_by_css_selector(self.selectable_days_selector)  # type: Sequence[WebElement]

		for elem in elems:
			assert isinstance(elem, WebElement)
			a = elem.find_element_by_tag_name('a')
			try:
				a = int(a.text)
			except ValueError:
				raise DatePickerError('Unable to find')
			if a == dt.day:
				elem.click()
				expected = dt.strftime('%m/%d/%Y')
				wait_for(lambda: self._browser.find_element_by_id(self.date_input_id).get_attribute('value') == expected, 2)
				return


	@property
	def _picker(self) -> WebElement:
		return self._get_from_browser()

	@property
	def current_datetime(self):
		return datetime.datetime(self.current_year, self.current_month, self.current_day)

	@property
	def current_month(self):
		self.displayed = True
		month_span = self._picker.find_element_by_css_selector(self.month_selector)
		return parser.parse(month_span.text).month

	@property
	def current_year(self):
		self.displayed = True
		year_span = self._picker.find_element_by_css_selector(self.year_selector)
		return int(year_span.text)

	@property
	def current_day(self):
		try:
			self.displayed = True
			day_td = self._picker.find_element_by_css_selector(self.day_selector)
			return int(day_td.text)
		except NoSuchElementException:
			raise ValueError('No current day.')

	def _check_is_displayed(self):
		picker_displayed = [self._picker.is_displayed()]
		elems = self._picker.find_elements_by_css_selector('td[data-handler="selectDay"]')
		# all_displayed = [select_day.is_displayed() and select_day.is_enabled() for select_day in elems]
		return picker_displayed and elems[-1].is_displayed()


	@property
	def displayed(self):
		return self._check_is_displayed()

	@displayed.setter
	def displayed(self, displayed: bool):
		if displayed and self.displayed:
			return
		elif displayed and not self.displayed:
			self._click_display_element()
			wait_for(self._check_is_displayed, 5)
		elif not displayed and self.displayed:
			self._click_display_element()
		elif not displayed and not self.displayed:
			return

	@property
	def previous_month_elem(self):
		self.displayed = True
		return self._picker.find_element_by_css_selector('a.ui-datepicker-prev')

	@property
	def next_month_elem(self):
		self.displayed = True
		return self._picker.find_element_by_css_selector('a.ui-datepicker-next')

	@property
	def at_earliest_month(self):
		return elem_has_class(self.previous_month_elem, 'ui-state-disabled')

	@property
	def at_latest_month(self):
		return elem_has_class(self.next_month_elem, 'ui-state-disabled')

	@property
	def current_highest_date(self):
		self.displayed = True
		tds = self._picker.find_elements_by_css_selector('td[data-handler="selectDay"]')
		highest_td = tds[-1]
		highest_a = highest_td.find_element_by_tag_name('a')
		day = int(highest_a.text)
		year = self.current_year
		month = self.current_month
		return datetime.date(year, month, day)

	@property
	def current_lowest_date(self):
		"""Note that this will be the lowest *selectable* date.  Lowest date will always be the 1st."""
		self.displayed = True
		tds = self._picker.find_elements_by_css_selector('td[data-handler="selectDay"]')
		lowest_td = tds[0]
		lowest_a = lowest_td.find_element_by_tag_name('a')
		day = int(lowest_a.text)
		year = self.current_year
		month = self.current_month
		return datetime.date(year, month, day)

	def go_to_date(self, dt: Union[datetime.datetime, datetime.date]):
		try:
			dt = dt.date()
		except AttributeError:
			pass

		while not self.is_date_on_current(dt):
			self.move_towards_date(dt)
		return True

	def is_date_on_current(self, dt: Union[datetime.datetime, datetime.date]):
		return self.current_lowest_date <= dt <= self.current_highest_date

	def is_date_lower_than_current(self, dt: Union[datetime.datetime, datetime.date]):
		return dt < self.current_lowest_date

	def is_date_higher_than_current(self, dt: Union[datetime.datetime, datetime.date]):
		return dt > self.current_highest_date

	def move_towards_date(self, dt: Union[datetime.datetime, datetime.date]) -> bool:
		"""Moves towards provided date.

        Would not move in the case of current displayed month being the correct month.

		:returns: True if moved, False if not.
		:raises InvalidDate: If date is not selectable.  Perhaps if it is on a month that
		is outside the limits of the datepicker.
		"""
		try:
			dt = dt.date()
		except AttributeError:
			pass

		result = False

		if self.is_date_lower_than_current(dt):
			result = self.go_to_previous_month()
			if not result:
				raise InvalidDate("Unable to move to previous month on datepicker.")
		elif self.is_date_higher_than_current(dt):
			result = self.go_to_next_month()
			if not result:
				raise InvalidDate("Unable to move to next month on datepicker.")
		return result

	def get_highest_date_avail(self):
		self.go_to_highest_month()
		return self.current_highest_date

	def get_lowest_date_avail(self):
		self.go_to_lowest_month()
		return self.current_lowest_date

	def go_to_previous_month(self) -> bool:
		"""
		Toggle to previous month.

		:return:  False if no change occurred (perhaps at least month supported) or
				  True if change occurred.
		"""
		if self.at_earliest_month:
			return False
		current_month = self.current_month
		self.previous_month_elem.click()
		wait_for(lambda: current_month != self.current_month, 2)
		return current_month != self.current_month

	def go_to_next_month(self) -> bool:
		"""
		Toggle to next month.

		:return:  False if no change occurred (perhaps at least month supported) or
				  True if change occurred.
		"""
		if self.at_latest_month:
			return False
		current_month = self.current_month
		self.next_month_elem.click()
		wait_for(lambda: current_month != self.current_month, 2)
		return current_month != self.current_month


	def go_to_lowest_month(self, limit=30):
		self._go_to_limit(go_up=False, limit=limit)

	def go_to_highest_month(self, limit=30):
		self._go_to_limit(limit=limit)

	def _go_to_limit(self, go_up: bool=True, limit: int=30):
		mover = self.go_to_next_month if go_up else self.go_to_previous_month
		for i in range(limit):
			if not mover():
				return

	def _click_display_element(self):
		self._check_have_click_to_display_element()
		self.click_to_display_element.click()

	def _check_have_click_to_display_element(self):
		assert self.click_to_display_element, "Cannot display datepicker if do not have `self.click_to_display_element`."

	def _get_from_browser(self) -> WebElement:
		pickers = self._browser.find_elements_by_css_selector(self.datepicker_selector)
		if len(pickers) > 1:
			raise ValueError("Too many pickers on page.  Provide css selector to specify which.")
		if len(pickers) == 0:
			raise ValueError("No pickers on page.  Possibly need another css selector?")

		return pickers[0]