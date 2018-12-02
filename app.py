from types import SimpleNamespace
from pathlib import Path
from urllib.parse import unquote
from os import environ
from os.path import abspath
from ast import literal_eval

from sanic import Sanic
from sanic.response import html, text
from jinja2 import Environment, FileSystemLoader, select_autoescape
from spotipy import Spotify as Spotipy
from spotipy.oauth2 import SpotifyClientCredentials as SCC
from htmlmin.minify import html_minify
from urlpath import URL as Url

from util import safe_execute

from bridges.github import GitHub, Repo, Org
from bridges.spotify import Spotify, Playlist
from bridges.blog import Blog

NAME = "philip-trauner.me"


env = SimpleNamespace()
ENV_VAR_PREFIX = "PT_"
DEFAULTS = {
    "ADDRESS": "0.0.0.0",
    "PORT": 5000,
    "DEBUG": False,
    "STATIC_HANDLER": True,
    "TEMPLATE_PATH": "template",
    "STATIC_URL": "https://static.philip-trauner.me",
    "BLOG_STATIC_URL": "https://blog.philip-trauner.me",
    "RSS_BASE_URL": "https://philip-trauner.me/blog/post",
    "RSS_URL": "https://philip-trauner.me/blog/rss",
    "ENABLE_GITHUB": False,
    "GITHUB_USER": "PhilipTrauner",
    "LIPSUM_GITHUB": True,
    "ENABLE_SPOTIFY": False,
    "SPOTIFY_USER": "philip.trauner",
    "SPOTIFY_CLIENT_ID": None,
    "SPOTIFY_CLIENT_SECRET": None,
    "LIPSUM_SPOTIFY": True,
}
for var in DEFAULTS:
    setattr(env, var.lower(), DEFAULTS[var])
for var in environ:
    if var.startswith(ENV_VAR_PREFIX):
        value = environ[var]
        setattr(
            env,
            var.lstrip(ENV_VAR_PREFIX).lower(),
            safe_execute(value, (ValueError, SyntaxError), lambda: literal_eval(value)),
        )


app = Sanic(NAME)

STATIC_URL = env.static_url
BLOG_STATIC_URL = env.blog_static_url
BLOG_PATH = Path("blog")

if env.static_handler:
    app.static("/static", "./dist")
    app.static("/blog/static/", str(BLOG_PATH / "post"))
    STATIC_URL = "/static/"
    BLOG_STATIC_URL = "/blog/static/"

STATIC_URL = Url(STATIC_URL)
BLOG_STATIC_URL = Url(BLOG_STATIC_URL)

jinja_env = Environment(
    loader=FileSystemLoader(env.template_path), trim_blocks=True, lstrip_blocks=True
)

spotify = (
    Spotify(
        env.spotify_user,
        Spotipy(
            client_credentials_manager=SCC(
                client_id=env.spotify_client_id, client_secret=env.spotify_client_secret
            )
        ),
    )
    if env.enable_spotify
    else (
        SimpleNamespace(playlists=[])
        if not env.lipsum_spotify
        else SimpleNamespace(playlists=[Playlist("Human Music", "", "")])
    )
)

github = (
    GitHub(env.github_user)
    if env.enable_github
    else (
        SimpleNamespace(repos=[], orgs=[])
        if not env.lipsum_github
        else SimpleNamespace(
            repos=[
                Repo("", "Name", 0, 100, True, True, "Description", None, "Brainfuck")
            ],
            orgs=[Org("Name", "", "Description", None)],
        )
    )
)

blog_ = Blog(
    BLOG_PATH,
    Url(BLOG_STATIC_URL),
    "Philip Trauner",
    "",
    "en-US",
    Url(env.rss_base_url),
    Url(env.rss_url),
)


# Wildcard route
@app.route("/")
@app.route("/<path>")
async def home(request, **kwargs):
    return html(
        html_minify(
            jinja_env.get_template("home.jinja").render(
                repos=github.repos,
                orgs=github.orgs,
                static_url=STATIC_URL,
                playlists=spotify.playlists,
                posts=blog_.posts,
                rss_url=env.rss_url,
            )
        )
    )


@app.route("/blog/post/<post>")
async def blog_post(request, post):
    post = blog_.find_post(unquote(post))

    return html(
        html_minify(
            jinja_env.get_template("blog-post.jinja").render(
                static_url=STATIC_URL,
                blog_static_url=BLOG_STATIC_URL,
                post=post,
                rss_url=env.rss_url,
            )
        ),
        status=200 if post else 404,
    )


@app.route("/blog/tag/<tag>")
async def blog_tag(request, tag):
    posts = blog_.find_posts_by_tag(unquote(tag))

    return html(
        html_minify(
            jinja_env.get_template("blog-tag.jinja").render(
                static_url=STATIC_URL, posts=posts, tag=tag
            )
        ),
        status=200 if len(posts) > 0 else 404,
    )


@app.route("/blog/rss")
async def blog_rss(request):
    return text(blog_.rss, headers={"Content-Type": "text/xml"})


try:
    app.run(host=env.address, port=env.port, debug=env.debug)
except KeyboardInterrupt:
    app.stop()
