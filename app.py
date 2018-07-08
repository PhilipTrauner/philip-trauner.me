from types import SimpleNamespace

from meh import Config, Option, ExceptionInConfigError
from sanic import Sanic
from sanic.response import html, text
from jinja2 import Template as JinjaTemplate
from spotipy import Spotify as Spotipy
from spotipy.oauth2 import SpotifyClientCredentials as SCC

from github_bridge import GitHub, Repo, Org
from spotify_bridge import Spotify, Playlist
from repl import Repl

NAME = "philip-trauner.me"
CONFIG_PATH = "philip-trauner.me.cfg"
DUMP_PATH = "github-dump.pickle"

PATH_HTML = "templates/index.min.html"


config = Config()
config += Option("address", "0.0.0.0")
config += Option("port", 5000)
config += Option("static_url", "")
config += Option("static_handler", False, comment="Serves static files")

config += Option("github_user", "PhilipTrauner")
config += Option("enable_github", True)

config += Option("spotify_user", "philip.trauner")
config += Option("spotify_client_id", None)
config += Option("spotify_client_secret", None)
config += Option("enable_spotify", True)

config += Option("debug", False)
config += Option("enable_repl", True)
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

spotify = (
    Spotify(
        config.spotify_user,
        Spotipy(
            client_credentials_manager=SCC(
                client_id=config.spotify_client_id,
                client_secret=config.spotify_client_secret,
            )
        ),
    )
    if config.enable_spotify
    else SimpleNamespace(playlists=[Playlist("Human Music", "", "")])
)

github = (
    GitHub(config.github_user, additional_repos=config.additional_repos)
    if config.enable_github
    else SimpleNamespace(
        repos=[Repo("", "Name", 0, 100, True, True, "Description", None, "Brainfuck")],
        orgs=[Org("Name", "", "Description", None)],
    )
)

if config.static_handler:
    app.static("/static", "./static")
    static_url = "static/"


@app.route("/")
async def home(request):
    return html(
        template.render(
            repos=github.repos,
            orgs=github.orgs,
            static_url=static_url,
            playlists=spotify.playlists,
        )
    )

"""
@app.route("/blog/<post>")
async def blog(request, post):
    return text(post)
"""

if config.enable_repl:
    repl = Repl()
    repl.start()

try:
    app.run(host=config.address, port=config.port, debug=config.debug)
except KeyboardInterrupt:
    app.stop()
