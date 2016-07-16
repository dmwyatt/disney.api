import json
import logging
import os
from pathlib import Path


_config = None

def _get_config(filepath: Path):
	global _config
	if _config is not None:
		return _config

	assert filepath.is_file(), "Cannot find %s." % str(filepath.absolute())

	with filepath.open('r') as f:
		_config = json.loads(f.read())
		return _config


class Config:
	def __init__(self, config_filepath, environ_prefix='DISNEY_API_'):
		self._data = _get_config(config_filepath)
		self.environ_prefix = environ_prefix

	@property
	def phantomjs_path(self):
		return self.get_from_config_or_environ('PHANTOM_PATH')

	@property
	def email_password(self):
		return self.get_from_config_or_environ('EMAIL_PASSWORD')

	@property
	def email_address(self):
		return self.get_from_config_or_environ('EMAIL_ADDRESS')

	@property
	def output(self):
		return self.get_from_config_or_environ('OUTPUT')

	@property
	def output_datetime_format(self):
		return self.get_from_config_or_environ('OUTPUT_DATETIME_FORMAT', default="%d/%m/%Y %H:%M")

	@property
	def singleton(self):
		return self.get_from_config_or_environ('MAKE_SINGLETON', default=True)

	@property
	def logging_level(self):
		levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

		value = self.get_from_config_or_environ('LOG_LEVEL', default="ERROR")
		assert value in levels, "Logging must be one of {}".format(levels)

		return value

	@property
	def restaurants_file(self):
		value = self.get_from_config_or_environ('RESTAURANTS_FILE', default="restaurants_config.json")
		return value

	@property
	def join_apikey(self):
		return self.get_from_config_or_environ('JOIN_APIKEY')

	@property
	def join_device_ids(self):
		return self.get_from_config_or_environ('JOIN_DEVICE_IDS')

	def get_from_config_or_environ(self, key, environ=None, default=None):
		if environ is None:
			environ = self.environ_prefix + key

		value = self._data.get(key)
		if value is None:
			value = os.environ.get(environ)
		if value is None:
			value = default
		return value


