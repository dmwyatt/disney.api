import datetime
import fcntl
import logging
import sys
from pathlib import Path
from pprint import pprint, pformat
from typing import List, Union, Sequence

import arrow
from selenium import webdriver

from config import Config
from join import Join, PlainTextualNotification
from notify_email import GmailHandler
from restaurants_config import RestaurantsConfigEntry

SINGLETON_ERR_CODE = 7

lf = None

def is_locked(lockfile):
	global lf
	lf = open(lockfile, 'w')
	try:
		fcntl.lockf(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
	except IOError:
		return False
	return True

def format_datetimes(datetimes: Sequence[Union[arrow.Arrow, datetime.datetime]],
                     dt_fmt: str) -> List[str]:
	return [x.strftime(dt_fmt) for x in datetimes]

def format_entries(entries: Sequence[RestaurantsConfigEntry], config: Config):
	# Get the times available for all of the restaurants
	entry_availabilities = {}
	for entry in entries:
		if not entry.availability_form.name in entry_availabilities:
			entry_availabilities[entry.availability_form.name] = []

		# Format the datetimes in configured manner
		formatted = format_datetimes(entry.get_times(), config.output_datetime_format)

		# We might have other times available for this restaurant already,
		# so we extend the existing list.
		entry_availabilities[entry.availability_form.name].extend(formatted)

	# We don't want the restaurants that don't have an available time
	nope = []
	for restaurant, availabilities in entry_availabilities.items():
		if not availabilities:
			nope.append(restaurant)

	for n in nope:
		del entry_availabilities[n]


def main(config: Config) -> None:
	browser = webdriver.PhantomJS(config.phantomjs_path)

	# Read in all of the entries in the list of restaurants
	entries = RestaurantsConfigEntry.get_many_from_json(config.restaurants_file, browser)

	entry_availabilities = format_entries(entries, config)


	if config.output == 'email' and entry_availabilities:
		gmail = GmailHandler(config.email_address, config.email_password)
		gmail.send_mail('dmwyatt@contriving.net', 'availabilities', pformat(entry_availabilities))

	elif not config.output and entry_availabilities:
		pprint(entry_availabilities)

	elif not config.output and not entry_availabilities:
		print('No times available.')

	if config.join_apikey and config.join_device_ids and entry_availabilities:
		j = Join(config.join_apikey)
		notification = PlainTextualNotification(pformat(entry_availabilities), title='Disney Availabilities')
		j.send(config.join_device_ids, notification=notification)

if __name__ == "__main__":
	config = Config(Path(sys.argv[1]))

	logging.basicConfig(level=config.logging_level)
	logging.getLogger('selenium').setLevel(logging.WARNING)

	if config.singleton:

		if is_locked('.lock'):
			main(config)
		else:
			sys.stderr.write('Already running\n')
			sys.exit(SINGLETON_ERR_CODE)
	else:
		main(config)