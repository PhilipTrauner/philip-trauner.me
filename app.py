from os.path import exists
from os import system
from pickle import dumps as pickle_dumps
from pickle import loads as pickle_loads

from meh import Config, Option, ExceptionInConfigError
from github_bridge import GitHub
from spotify_bridge import Spotify
from sanic import Sanic
from sanic.response import html
from jinja2 import Template as JinjaTemplate

from spotipy import Spotify as Spotipy
from spotipy.oauth2 import SpotifyClientCredentials as SCC

NAME = "philip-trauner.me"
CONFIG_PATH = "philip-trauner.me.cfg"
DUMP_PATH = "github-dump.pickle"

PATH_HTML = "templates/index.min.html"


config = Config()
config += Option("address", "0.0.0.0")
config += Option("port", 5000)
config += Option("github_user", "PhilipTrauner")
config += Option("spotify_user", "philip.trauner")
config += Option("static_url", "")
config += Option("static_handler", False, comment="Serves static files")
config += Option("cache_github", False, comment="Caches repos and orgs")
config += Option("spotify_client_id", None)
config += Option("spotify_client_secret", None)
config += Option("debug", False)
config += Option("additional_repos", [], comment="Additional repos")

try:
    config = config.load(CONFIG_PATH)
except (IOError, ExceptionInConfigError):
    config.dump(CONFIG_PATH)
    config = config.load(CONFIG_PATH)


if config.static_url != "":
	if config.static_url[-1] != "/":
		config.static_url = config.static_url + "/"

static_url = str(config.static_url)

template = JinjaTemplate(open(PATH_HTML).read())
app = Sanic(NAME)

spotify = Spotify(config.spotify_user, 
	Spotipy(client_credentials_manager=SCC(client_id=config.spotify_client_id, 
		client_secret=config.spotify_client_secret)))

if config.cache_github:
	if not exists(DUMP_PATH):
		github = GitHub(config.github_user, 
			additional_repos=config.additional_repos)
		github.force_fetch()
		open(DUMP_PATH, "wb").write(pickle_dumps(github))
	else:
		github = pickle_loads(open(DUMP_PATH, "rb").read())
		github.disable_fetch = True
else:
	github = GitHub(config.github_user, additional_repos=config.additional_repos)

if config.static_handler:
	app.static('/static', './static')
	static_url = "static/"


@app.route("/")
async def home(request):
	return html(template.render(repos=github.repos, orgs=github.orgs, 
		static_url=static_url, playlists=spotify.playlists))

try:
	app.run(host=config.address, port=config.port, debug=config.debug)
except KeyboardInterrupt:
	app.stop()