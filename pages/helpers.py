import time

from selenium.webdriver.remote.webelement import WebElement


class WaitError(Exception):
	pass


def wait_for(func, timeout):
	timeout_start = time.time()
	while True:
		if func():
			return
		time.sleep(.25)
		if time.time() >= timeout_start + timeout:
			raise WaitError()


def elem_has_class(elem: WebElement, className: str):
	classes = elem.get_attribute('class')
	classes = classes.split()
	return className in classes