import logging
from typing import Sequence, Any, MutableMapping

import requests


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

JOIN_URL = "https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush"

class Join:
	VALID_GROUPS = ["group.all",
	                "group.android",
	                "group.chrome",
	                "group.windows10",
	                "group.phone",
	                "group.tablet",
	                "group.pc"]
	def __init__(self, apikey: str):
		self.apikey = apikey

	@property
	def params(self):
		return dict(apikey=self.apikey)

	def send(self, device_ids: Sequence[str],
	         text: str=None,
	         title: str=None,
	         icon: str=None,
	         smallicon: str=None,
	         notification: 'PlainTextualNotification'=None,
	         url: str=None,
	         clipboard: str=None,
	         file_: str=None,
	         smsnumber: str=None,
	         smstext: str=None,
	         wallpaper: str=None,
	         find: bool=False):

		assert hasattr(device_ids, '__iter__'), "must provide sequence of device ids"

		device_ids = list(set(device_ids))

		params = self.params
		self._add2(params, text=text, title=title, icon=icon, smallicon=smallicon,
		           url=url, clipboard=clipboard, file=file_, smsnumber=smsnumber,
		           smstext=smstext, wallpaper=wallpaper)
		if find:
			self._add('find', 'true', params)

		self._add_obj_params(notification, params)

		groups = []
		for group in self.VALID_GROUPS:
			if group in device_ids:
				groups.append(group)
				device_ids.remove(group)

		# Join API won't let us mix groups with deviceIds, so we need
		# to do a separate request for each group.
		responses = {}
		for group in groups:
			group_params = dict(params)
			group_params['deviceId'] = group
			responses[group] = requests.get(JOIN_URL, params=group_params)

		if len(device_ids) > 1:
			self._add('deviceIds', ",".join(device_ids), params)

		elif len(device_ids) == 1:
			self._add('deviceId', device_ids[0], params)

		if device_ids:
			responses[tuple(device_ids)] = requests.get(JOIN_URL, params=params)

		return responses

	def find_device(self, device_id: str):
		return self.send(device_ids=[device_id], find=True)

	def ring_device(self, device_id: str):
		return self.find_device(device_id)

	def send_url(self, device_id: str, url: str, notification: 'PlainTextualNotification'=None):
		"""
		Send url to the device.

		*  If `notification` is None and device is locked, creates a notification that
		opens browser with url when clicked.

		*  If `notification` is None and device is unlocked, opens browser with url.

		* If `notification` is provided and device is locked, creates notification
		 which opens url when clicked.

		* If `notification` is provided and device is unlocked, creates notification
		 and also opens browser with url.
		"""
		self.send([device_id], url=url, notification=notification)

	def send_to_clipboard(self,
	                      device_id: str,
	                      clipboard: str,
	                      notification: 'PlainTextualNotification'=None):
		"""
		Send text to clipboard on device.

		To provide a notification to the device user provide notification_text
		and/or notification_title.  Otherwise, the text is just dumped into
		the device clipboard with no notice to device user.
		"""
		return self.send([device_id],
		                 clipboard=clipboard,
		                 notification=notification)

	def _add(self, key: str, value: Any, d: MutableMapping[str, Any]):
		if value:
			d[key] = value

	def _add_obj_params(self, params_haver, d: MutableMapping[str, Any]) -> MutableMapping:
		if not params_haver:
			return
		params = params_haver.get_params()
		for k, v in params.items():
			self._add(k, v, d)

	def _add2(self, d: MutableMapping[str, Any], **kwargs):
		for k, v in kwargs.items():
			if v is not None:
				d[k] = v


class JoinNotification:
	def __init__(self, apikey: str, deviceids: Sequence[str]):
		self.join = Join(apikey)
		self.text = None
		self.title = None
		self.icon = None
		self.smallicon = None
		self.url = None
		self.clipboard = None
		self.file = None
		self.smsnumber = None
		self.smstext = None
		self.wallpaper = None
		self.find = None


class PlainTextualNotification:
	def __init__(self, text: str, title: str=None, icon: str=None, smallicon: str=None):
		self.text = text
		assert self.text, "Must always include `text` with a notification."
		self.title = title
		self.icon = icon
		self.smallicon = icon

	def get_params(self):
		params = {'text': self.text}
		if self.title:
			params['title'] = self.title
		if self.icon:
			params['icon'] = self.icon
		if self.smallicon:
			params['smallicon'] = self.smallicon
		return params
