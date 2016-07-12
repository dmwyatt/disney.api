class URLS:
	restaurants = 'https://disneyworld.disney.go.com/dining/'
	token = 'https://disneyworld.disney.go.com/authentication/get-client-token/'
	availability = 'https://disneyworld.disney.go.com/finder/dining-availability/'

DEFAULT_HEADER = {'X-Requested-With': 'XMLHttpRequest'}

try:
	import lxml
	BS_LEXER = 'lxml'
except ImportError:
	BS_LEXER = 'html.parser'

KEYRING_SERVICE = 'disney.api'