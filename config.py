import json
import logging
import os
from pathlib import Path


config = None

def get_config(filepath=None):
	global config
	if config is not None:
		return config

	config_file_name = 'config.json'

	if filepath is None:
		filepath = './{}'.format(config_file_name)

	filepath = Path(filepath)

	assert filepath.is_file(), "Cannot find %s." % str(filepath.absolute())

	with filepath.open('r') as f:
		config = json.loads(f.read())
		return config


class Config:
	def __init__(self, environ_prefix='DISNEY_API_', filepath=None):
		self._data = get_config(filepath=filepath)
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
		value = self.get_from_config_or_environ('LOG_LEVEL', default="ERROR")
		return getattr(logging, value)

	@property
	def restaurants_file(self):
		value = self.get_from_config_or_environ('RESTAURANTS_FILE', default="restaurants_config.json")
		return value

	def get_from_config_or_environ(self, key, environ=None, default=None):
		if environ is None:
			environ = self.environ_prefix + key

		value = self._data.get(key)
		if value is None:
			value = os.environ.get(environ)
		if value is None:
			value = default
		return value


