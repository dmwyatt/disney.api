import json
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

	assert filepath.is_file(), "Cannot find %s." % config_file_name

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
		value = self.get_from_config_or_environ('OUTPUT_DATETIME_FORMAT')
		if value is None:
			return "%d/%m/%Y %H:%M"
		return value

	def get_from_config_or_environ(self, key, environ=None):
		if environ is None:
			environ = self.environ_prefix + key

		value = self._data.get(key)
		if value is None:
			return os.environ.get(environ)
		return value

