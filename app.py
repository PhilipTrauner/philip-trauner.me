from pathlib import Path
from urllib.parse import unquote

from jinja2 import Environment
from jinja2 import FileSystemLoader
from sanic import Sanic
from sanic.response import html
from sanic.response import text
from spotipy import Spotify as Spotipy
from spotipy.oauth2 import SpotifyClientCredentials as SCC
from environs import Env

from bridges.blog import Blog
from bridges.blog.util import Url
from bridges.github import GitHub
from bridges.spotify import Spotify


NAME = "philip-trauner.me"

DEFAULT_PUBLIC_URL = "/static/public"
DEFAULT_BLOG_STATIC_URL = "/static/blog/post"

RSS_ROUTE = "blog/rss"
RSS_POST_ROUTE_PARTIAL = "blog/post"

env = Env()


@env.parser_for("furl")
def url_parser(value: str) -> Url:
    return Url(value)


with env.prefixed("PT_"):
    address = env.str("ADDRESS", "0.0.0.0")
    port = env.int("PORT", 5000)
    debug = env.bool("DEBUG", False)
    static_handler = env.bool("ENABLE_STATIC_HANDLER", True)
    blog_path = env.path("BLOG_PATH", "./blog")
    public_url = env.furl("PUBLIC_URL", DEFAULT_PUBLIC_URL)
    blog_static_url = env.furl("BLOG_STATIC_URL", DEFAULT_BLOG_STATIC_URL)
    fq_url = env.furl("FQ_URL", f"http://localhost:{port}")

    # Disabled by default because rate limit can be hit relatively easily
    # during development
    enable_github = env.bool("ENABLE_GITHUB", False)
    github_user = env.str("GITHUB_USER", "PhilipTrauner")
    # Disabled by default because credentials are necessary
    enable_spotify = env.bool("ENABLE_SPOTIFY", False)
    spotify_user = env.str("SPOTIFY_USER", "philip.trauner")
    spotify_client_id = env.str("SPOTIFY_CLIENT_ID", None)
    spotify_client_secret = env.str("SPOTIFY_CLIENT_SECRET", None)

app = Sanic(NAME)

if static_handler:
    app.static(DEFAULT_PUBLIC_URL, "./public")
    app.static(DEFAULT_BLOG_STATIC_URL, str(blog_path / "post"))

transformed_public_url = Url(public_url)
transformed_blog_static_url = Url(blog_static_url)

jinja_env = Environment(
    loader=FileSystemLoader([str(Path("template")), str(Path("dist"))]),
    # https://github.com/hyde/hyde-old/issues/68
    comment_start_string="{##",
    comment_end_string="##}",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=True,
)

spotify = (
    Spotify(
        spotify_user,
        Spotipy(
            client_credentials_manager=SCC(
                client_id=spotify_client_id, client_secret=spotify_client_secret
            )
        ),
    )
    if enable_spotify
    else None
)

github = GitHub(github_user) if enable_github else None

rss_url = fq_url / RSS_ROUTE

blog = Blog(
    blog_path,
    transformed_blog_static_url,
    "Philip Trauner",
    "",
    "en-US",
    fq_url / RSS_POST_ROUTE_PARTIAL,
    rss_url,
)


# Wildcard route
@app.route("/")
# Necessitates `**kwargs` necessary
@app.route("/<path>")
async def home(_, **kwargs):
    return html(
        jinja_env.get_template("home.jinja").render(
            repos=github.repos if github is not None else [],
            public_url=transformed_public_url,
            playlists=spotify.playlists if spotify is not None else [],
            posts=blog.posts,
            rss_url=rss_url,
        )
    )


@app.route(f"{RSS_POST_ROUTE_PARTIAL}/<post>")
async def blog_post(_, post):
    post = blog.find_post(unquote(post))

    return html(
        jinja_env.get_template("blog-post.jinja").render(
            public_url=transformed_public_url,
            blog_static_url=transformed_blog_static_url,
            post=post,
            rendered=post.render(transformed_blog_static_url)
            if post is not None
            else None,
            rss_url=rss_url,
        ),
        status=200 if post else 404,
    )


@app.route("/blog/tag/<tag>")
async def blog_tag(_, tag):
    posts = blog.find_posts_by_tag(unquote(tag))

    return html(
        (
            jinja_env.get_template("blog-tag.jinja").render(
                public_url=transformed_public_url, posts=posts, tag=tag
            )
        ),
        status=200 if len(posts) > 0 else 404,
    )


@app.route(RSS_ROUTE)
async def blog_rss(_):
    return text(blog.rss, headers={"Content-Type": "text/xml"})


try:
    app.run(host=address, port=port, debug=debug)
except KeyboardInterrupt:
    app.stop()
