from types import SimpleNamespace
from pathlib import Path
from urllib.parse import unquote
from os import environ

from meh import Config, Option, ExceptionInConfigError
from sanic import Sanic
from sanic.response import html, text
from jinja2 import Environment, FileSystemLoader, select_autoescape
from spotipy import Spotify as Spotipy
from spotipy.oauth2 import SpotifyClientCredentials as SCC
from htmlmin.minify import html_minify
from urlpath import URL as Url

from bridges.github import GitHub, Repo, Org
from bridges.spotify import Spotify, Playlist
from bridges.blog import Blog

NAME = "philip-trauner.me"
CONFIG_PATH = "app.cfg"

IN_DOCKER = environ.get("IN_DOCKER", False)

config = Config()
config += Option("address", "0.0.0.0")
config += Option("port", 5000)
config += Option("static_handler", False)

config += Option("static_url", "https://static.philip-trauner.me")

config += Option("blog_static_url", "https://blog.philip-trauner.me")
config += Option("rss_base_url", "https://philip-trauner.me/blog/post")
config += Option("rss_url", "https://philip-trauner.me/blog/rss")

config += Option("github_user", "PhilipTrauner")
config += Option("enable_github", True)
config += Option("lipsum_github", False)

config += Option("spotify_user", "philip.trauner")
config += Option("spotify_client_id", None)
config += Option("spotify_client_secret", None)
config += Option("enable_spotify", True)
config += Option("lipsum_spotify", False)

config += Option("debug", False)
config += Option("additional_repos", [], comment="Additional repos")

try:
    config = config.load(CONFIG_PATH)
except (IOError, ExceptionInConfigError):
    if not IN_DOCKER:
        config.dump(CONFIG_PATH)
        config = config.load(CONFIG_PATH)
    else:
        print("Config files are not created automatically when running in Docker.")
        exit(0)

app = Sanic(NAME)

if config.static_handler:
    app.static("/static", "./dist")
    static_url = "/static/"
    app.static("/blog/static/", "./posts/")
    blog_static_url = "/blog/static/"
else:
    static_url = config.static_url
    blog_static_url = config.blog_static_url

env = Environment(
    loader=FileSystemLoader("src/template"), trim_blocks=True, lstrip_blocks=True
)

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
    else (
        SimpleNamespace(playlists=[])
        if not config.lipsum_spotify
        else SimpleNamespace(playlists=[Playlist("Human Music", "", "")])
    )
)

github = (
    GitHub(config.github_user, additional_repos=config.additional_repos)
    if config.enable_github
    else (
        SimpleNamespace(repos=[], orgs=[])
        if not config.lipsum_github
        else SimpleNamespace(
            repos=[
                Repo("", "Name", 0, 100, True, True, "Description", None, "Brainfuck")
            ],
            orgs=[Org("Name", "", "Description", None)],
        )
    )
)

blog_ = Blog(
    Path("posts"), Url(blog_static_url), Url(config.rss_base_url), Url(config.rss_url)
)


# Wildcard route
@app.route("/")
@app.route("/<path>")
async def home(request, **kwargs):
    return html(
        html_minify(
            env.get_template("home.html").render(
                repos=github.repos,
                orgs=github.orgs,
                static_url=static_url,
                playlists=spotify.playlists,
                posts=blog_.posts,
                rss_url=config.rss_url,
            )
        )
    )


@app.route("/blog/post/<post>")
async def blog_post(request, post):
    post = blog_.find_post(unquote(post))

    return html(
        html_minify(
            env.get_template("blog-post.html").render(
                static_url=static_url,
                blog_static_url=blog_static_url,
                post=post,
                rss_url=config.rss_url,
            )
        ),
        status=200 if post else 404,
    )


@app.route("/blog/tag/<tag>")
async def blog_tag(request, tag):
    posts = blog_.find_posts(unquote(tag))

    return html(
        html_minify(
            env.get_template("blog-tag.html").render(
                static_url=static_url, posts=posts, tag=tag
            )
        ),
        status=200 if len(posts) > 0 else 404,
    )


@app.route("/blog/rss")
async def blog_rss(request):
    return text(blog_.rss, headers={"Content-Type": "text/xml"})


try:
    app.run(host=config.address, port=config.port, debug=config.debug)
except KeyboardInterrupt:
    app.stop()
