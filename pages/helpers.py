import time
from typing import Callable

from selenium.webdriver.remote.webelement import WebElement


class WaitError(Exception):
	pass


def wait_for(test: Callable[[], bool],
             timeout: int,
             test_interval: float = .25,
             on_success: Callable[[], None] = lambda: None,
             on_failure: Callable[[], None] = lambda: None):
	timeout_start = time.time()
	while True:
		if test():
			on_success()
			return
		time.sleep(test_interval)
		if time.time() >= timeout_start + timeout:
			on_failure()
			raise WaitError()


def elem_has_class(elem: WebElement, className: str):
	classes = elem.get_attribute('class')
	classes = classes.split()
	return className in classes
