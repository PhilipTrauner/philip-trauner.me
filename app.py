from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import unquote

from htmlmin.minify import html_minify
from jinja2 import Environment
from jinja2 import FileSystemLoader
from sanic import Sanic
from sanic.response import html
from sanic.response import text
from spotipy import Spotify as Spotipy
from spotipy.oauth2 import SpotifyClientCredentials as SCC
from urlpath import URL as Url

from bridges.blog import Blog
from bridges.github import GitHub
from bridges.github import Org
from bridges.github import Repo
from bridges.spotify import Playlist
from bridges.spotify import Spotify
from env import build_env
from env import Default

NAME = "philip-trauner.me"


def bool_validator(value: Any) -> bool:
    return type(value) is bool


def url_transform(value: Any) -> Url:
    return Url(value)


env = build_env(
    "PT_",
    {
        "ADDRESS": Default("0.0.0.0"),
        "PORT": Default(5000, validator=lambda value: type(value) is int and value > 0),
        "DEBUG": Default(False, validator=bool_validator),
        "STATIC_HANDLER": Default(True, validator=bool_validator),
        "TEMPLATE_PATH": Default(
            Path("template").resolve(),
            transformer=lambda value: Path(value).resolve(),
            validator=lambda value: value.is_dir(),
        ),
        "BLOG_PATH": Default(
            Path("blog").resolve(),
            transformer=lambda value: Path(value).resolve(),
            validator=lambda value: value.is_dir(),
        ),
        "STATIC_URL": Default(
            "https://static.philip-trauner.me", transformer=url_transform
        ),
        "BLOG_STATIC_URL": Default(
            "https://blog.philip-trauner.me", transformer=url_transform
        ),
        "RSS_BASE_URL": Default(
            "https://philip-trauner.me/blog/post", transformer=url_transform
        ),
        "RSS_URL": Default(
            "https://philip-trauner.me/blog/rss", transformer=url_transform
        ),
        "ENABLE_GITHUB": Default(False, validator=bool_validator),
        "GITHUB_USER": Default("PhilipTrauner"),
        "LIPSUM_GITHUB": Default(True, validator=bool_validator),
        "ENABLE_SPOTIFY": Default(False, validator=bool_validator),
        "SPOTIFY_USER": Default("philip.trauner"),
        "SPOTIFY_CLIENT_ID": Default(
            None, validator=lambda value: value is None or type(value) is str
        ),
        "SPOTIFY_CLIENT_SECRET": Default(
            None, validator=lambda value: value is None or type(value) is str
        ),
        "LIPSUM_SPOTIFY": Default(True, validator=bool_validator),
    },
)


app = Sanic(NAME)

STATIC_URL = env.static_url
BLOG_STATIC_URL = env.blog_static_url
BLOG_PATH = env.blog_path

if env.static_handler:
    app.static("/static", "./dist")
    app.static("/blog/static/", str(BLOG_PATH / "post"))
    STATIC_URL = "/static/"
    BLOG_STATIC_URL = "/blog/static/"

STATIC_URL = Url(STATIC_URL)
BLOG_STATIC_URL = Url(BLOG_STATIC_URL)

jinja_env = Environment(
    loader=FileSystemLoader(str(env.template_path)),
    trim_blocks=True,
    lstrip_blocks=True,
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
