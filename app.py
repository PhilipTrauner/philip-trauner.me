from pathlib import Path
from urllib.parse import unquote

from environs import Env
from jinja2 import Environment, FileSystemLoader
from sanic import Sanic
from sanic.response import html, text

from bridges.blog import Blog
from bridges.blog.util import Url

DEFAULT_PUBLIC_URL = "/static/public"
DEFAULT_BLOG_STATIC_URL = "/static/blog/post"

RSS_ROUTE = "blog/rss"
RSS_POST_ROUTE_PARTIAL = "blog/post"

env = Env()


@env.parser_for("furl")
def url_parser(value: str) -> Url:
    return Url(value)


with env.prefixed("PT_"):
    address = env.str("ADDRESS", "127.0.0.1")
    port = env.int("PORT", 3000)
    debug = env.bool("DEBUG", False)
    blog_path = env.path("BLOG_PATH", Path("./blog"))
    blog_observe = env.bool("BLOG_OBSERVE", True)
    public_url = env.furl("PUBLIC_URL", DEFAULT_PUBLIC_URL)
    blog_static_url = env.furl("BLOG_STATIC_URL", DEFAULT_BLOG_STATIC_URL)
    fq_url = env.furl("FQ_URL", f"http://localhost:{port}")

app = Sanic(name="app")

app.static(DEFAULT_PUBLIC_URL, "./public", name="public")
app.static(DEFAULT_BLOG_STATIC_URL, str(blog_path / "post"), name="blog_static")

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

rss_url = fq_url / RSS_ROUTE

blog = Blog(
    blog_path,
    transformed_blog_static_url,
    "Philip Trauner",
    "",
    "en-US",
    fq_url / RSS_POST_ROUTE_PARTIAL,
    rss_url,
    blog_observe,
)


# Wildcard route
@app.route("/", name="root")
# Necessitates `**kwargs` necessary
@app.route("/<path>", name="home")
async def home(_, **kwargs):
    return html(
        jinja_env.get_template("home.jinja").render(
            public_url=transformed_public_url,
            posts=blog.posts,
            rss_url=rss_url,
        )
    )


@app.route(f"{RSS_POST_ROUTE_PARTIAL}/<post>", name="post")
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


@app.route("/blog/tag/<tag>", name="tag")
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


@app.route(RSS_ROUTE, name="rss")
async def blog_rss(_):
    return text(blog.rss, headers={"Content-Type": "text/xml"})


try:
    app.run(host=address, port=port, debug=debug, single_process=True)
except KeyboardInterrupt:
    app.stop()
