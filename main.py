import logging
from pprint import pprint, pformat
from typing import List, Union, Sequence

import datetime

import arrow

from config import Config
from notify_email import GmailHandler
from restaurants_config import RestaurantsConfigEntry

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('selenium').setLevel(logging.WARNING)

def format_datetimes(datetimes: Sequence[Union[arrow.Arrow, datetime.datetime]],
                     dt_fmt: str) -> List[str]:
	return [x.strftime(dt_fmt) for x in datetimes]

def main(config: Config) -> None:
	entries = RestaurantsConfigEntry.get_many_from_json('restaurants_config.json')

	entry_availabilities = {}
	for entry in entries:
		if not entry.availability_form.name in entry_availabilities:
			entry_availabilities[entry.availability_form.name] = []
		formatted = format_datetimes(entry.get_times(), config.output_datetime_format)
		entry_availabilities[entry.availability_form.name].extend(formatted)

	if config.output == 'email':
		gmail = GmailHandler(config.email_address, config.email_password)
		gmail.send_mail('dmwyatt@contriving.net', 'availabilities', pformat(entry_availabilities))
	else:
		pprint(entry_availabilities)

if __name__ == "__main__":
	config = Config()

	main(Config())