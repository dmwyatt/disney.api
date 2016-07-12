import json

import re

import bs4
import requests
from bs4 import BeautifulSoup

from constants import DEFAULT_HEADER, BS_LEXER
from constants import URLS


RD_HEADERS = dict(DEFAULT_HEADER)
RD_HEADERS['Referer'] = URLS.restaurants

class RestaurantListPage:
	def __init__(self, content):
		self.soup = BeautifulSoup(content, BS_LEXER)


		#cached properties
		self._cards = None
		self._finder_blob = None
		self._restaurants = None

	@property
	def restaurants(self):
		if self._restaurants is None:
			self._restaurants = {}
			for card in self.cards.values():
				self._restaurants[card.entity_id] = RestaurantData(card, self.finder_data['cards'][card.entity_id])

		return self._restaurants

	@property
	def cards(self):
		if self._cards is None:
			cards = self.soup.select('li.card.dining')
			cards = [RestaurantCard(card) for card in cards]
			self._cards = {card.entity_id: card for card in cards}

		return self._cards

	@property
	def finder_data(self):
		if self._finder_blob is None:
			finder = self.soup.select('script#finderBlob')
			finder = str(finder[0])
			self._finder_blob = re.search('^ {1,10}PEP\.Finder\.List ?= ?({.*});$', finder, flags=re.MULTILINE).groups()[0]
			self._finder_blob = json.loads(self._finder_blob)

		return self._finder_blob

	@classmethod
	def get_page(cls, session: requests.Session):
		response = session.get(URLS.restaurants, headers=RD_HEADERS)
		assert response.status_code == 200, 'Unable to get restaurants list.'

		return cls(response.text)

class RestaurantCard:
	def __init__(self, soup):
		if isinstance(soup, bs4.element.Tag):
			self.soup = soup
		elif isinstance(soup, list) and len(soup) == 1 and isinstance(soup[0], bs4.element.Tag):
			self.soup = soup
		else:
			raise ValueError('Do not know how to get BeautifulSoup object from type: {}'.format(type(soup)))

		first_div = soup('div')[0]
		self.name = first_div['aria-label']
		self.url = first_div.get('data-href')
		self.entity_id = soup.get('data-entityid')
		assert self.entity_id, "Unable to extract ID from: \n{}".format(str(soup))

class RestaurantData:
	def __init__(self, card: RestaurantCard, data):
		self._card = card
		self._data = data
		self._facets = self._data.get('facets')

		self.name = self._card.name
		self.url = getattr(self._card, 'url', None)
		self.entity_id = self._card.entity_id

		self.cuisine = None
		self.themepark = None
		self.dining_plans = []
		self.price_range = None
		if self._facets:
			cuisine = self._facets.get('cuisine', {})
			self.cuisine = cuisine.get('text', None)

			themepark = self._facets.get('theme-park', {})
			self.themepark = themepark.get('text', None)

			dining_plans = self._facets.get('diningPlan', {'text': ''})
			self.dining_plans = [dp.strip() for dp in dining_plans.get('text').split(',')]

			price_range = self._facets.get('priceRangeDining', {})
			self.price_range = price_range.get('key')


