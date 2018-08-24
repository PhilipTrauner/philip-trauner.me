from pathlib import Path
from threading import Lock
from json import loads as json_loads
from json.decoder import JSONDecodeError
from datetime import datetime
from re import compile as re_compile
from typing import Callable, List, Optional, Tuple, Type, Dict, Any


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler as WatchdogFileSystemEventHandler

from mistune import Renderer as MistuneRenderer
from mistune import Markdown as MistuneMarkdown
from mistune import escape as mistune_escape

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html

from urlpath import URL as Url

from rfeed import Feed, Item, Guid

WARNING_COLOR = "\033[33m"
EMPHASIS_COLOR = "\033[35m"
ANSI_END = "\033[0m"

LICENSE_VERSION = "4.0"

LICENSE_BASE_URL = "https://creativecommons.org/licenses/"
LICENSE_END_URL = "%s/" % LICENSE_VERSION

LICENSE_IMAGE_BASE_URL = "https://licensebuttons.net/i/l/"
LICENSE_IMAGE_END_URL = "transparent/00/00/00/88x31.png"

VALID_MARKDOWN = re_compile(r"^#.*$")
FIND_IMAGE = re_compile(r"(?:!\[.*\]\(([^)]*)\))|(?:<img.*src=\"([^\"]*))")
IMAGE_REWRITE = [
    re_compile(r"(<img.*src=\")([^\"]*)(.*)"),  # <img src="image.png" />
    re_compile(r"(!\[.*\]\()([^)]*)(\))"),  # ![](image.png)
]
HAS_CODE = re_compile(r"```\w+\n")

CONTENT_FOLDER = "content"
BLOG_METADATA = "metadata.json"
BLOG_TEXT = "text.md"


def all_match_condition(function: Callable, iterable: List[str]) -> bool:
    for element in iterable:
        if not function(element):
            return False
    return True


# https://stackoverflow.com/questions/36671077/one-line-exception-handling/36671208
def safe_execute(default, exception, function, *args):
    try:
        return function(*args)
    except exception:
        return default


def _cc_license_urls(license_string) -> Tuple[Url, Url]:
    return (
        Url(LICENSE_BASE_URL) / license_string / LICENSE_END_URL,
        Url(LICENSE_IMAGE_BASE_URL) / license_string / LICENSE_IMAGE_END_URL,
    )


class License:
    def __init__(self, name: str, description_url: Url) -> None:
        self.name = name
        self.description_url = description_url


class TextLicense(License):
    def __init__(self, name: str, description_url: Url, image_url: Url) -> None:
        super().__init__(name, description_url)
        self.image_url = image_url


class CodeLicense(License):
    def __init__(self, name: str, description_url: Url) -> None:
        super().__init__(name, description_url)


TEXT_LICENSES: Dict[str, License] = {
    "by-nc-nd": TextLicense(
        "Attribution-NonCommercial-NoDerivatives 4.0 International",
        *_cc_license_urls("by-nc-nd")
    ),
    "by-nc-sa": TextLicense(
        "Attribution-NonCommercial-ShareAlike 4.0 International",
        *_cc_license_urls("by-nc-sa")
    ),
    "by-nc": TextLicense(
        "Attribution-NonCommercial 4.0 International", *_cc_license_urls("by-nc")
    ),
    "by-nd": TextLicense(
        "Attribution-NoDerivatives 4.0 International", *_cc_license_urls("by-nd")
    ),
    "by-sa": TextLicense(
        "Attribution-ShareAlike 4.0 International", *_cc_license_urls("by-sa")
    ),
    "by": TextLicense("Attribution 4.0 International", *_cc_license_urls("by")),
}

CODE_LICENSES: Dict[str, CodeLicense] = {
    "mit": CodeLicense("MIT", Url("https://choosealicense.com/licenses/mit/"))
}

VALID_TEXT_LICENSE_STRINGS: List[str] = list(TEXT_LICENSES.keys())
VALID_CODE_LICENSE_STRINGS: List[str] = list(CODE_LICENSES.keys())


class Date:
    def __init__(self, unix_date: int) -> None:
        self.unix_date = unix_date
        self.datetime = datetime.fromtimestamp(unix_date)
        self.pretty_date = self.datetime.strftime("%B %d, %Y")
        self.iso_date = self.datetime.strftime("%Y-%m-%d %H:%M:%S")


class Image:
    class _Image:
        def __init__(self, path: str, url: Url) -> None:
            self.path = path
            self.url = url

    def __new__(cls: Type["Image"], path: Path, image_base_url: Url):
        return Image._Image(path.absolute(), image_base_url / path.name)


class PostMetadata:
    class _PostMetadata:
        def __init__(
            self,
            date: Date,
            tags: List[str],
            text_license: TextLicense,
            code_license: Optional[CodeLicense],
            description: str,
            section: str,
            author: str,
            hidden: bool,
        ) -> None:
            self.date = date
            self.tags = tags
            self.text_license = text_license
            self.code_license = code_license
            self.description = description
            self.section = section
            self.author = author
            self.hidden = hidden

    def __new__(
        cls: Type["PostMetadata"], metadata_path: Path, post_has_code: bool
    ) -> Optional["PostMetadata._PostMetadata"]:
        if PostMetadata.valid(metadata_path, post_has_code):
            metadata_dict = json_loads(open(metadata_path, "r").read())
            return PostMetadata._PostMetadata(
                Date(metadata_dict["date"]),
                metadata_dict["tags"],
                TEXT_LICENSES[metadata_dict["license"]["text"]],
                CODE_LICENSES[metadata_dict["license"]["code"]]
                if post_has_code
                else None,
                metadata_dict["description"],
                metadata_dict["section"],
                metadata_dict["author"],
                metadata_dict.get("hidden", False),
            )
        return None

    @staticmethod
    def valid(metadata_path: Path, post_has_code: bool) -> bool:
        metadata_dict = safe_execute(
            None, JSONDecodeError, json_loads, open(metadata_path, "r").read()
        )

        return (
            type(metadata_dict) is dict
            and "date" in metadata_dict
            and type(metadata_dict["date"]) is int
            and metadata_dict["date"] > 0
            and "tags" in metadata_dict
            and type(metadata_dict["tags"]) is list
            and all_match_condition(
                lambda element: type(element) is str, metadata_dict["tags"]
            )
            and "license" in metadata_dict
            and "text" in metadata_dict["license"]
            and metadata_dict["license"]["text"] in VALID_TEXT_LICENSE_STRINGS
            and (
                "license" in metadata_dict
                and "code" in metadata_dict["license"]
                and metadata_dict["license"]["code"] in VALID_CODE_LICENSE_STRINGS
            )
            if post_has_code
            else True
            and "description" in metadata_dict
            and "section" in metadata_dict
            and "author" in metadata_dict
        )


class Post:
    class _Post:
        def __init__(
            self,
            name: str,
            title: str,
            post_metadata: PostMetadata._PostMetadata,
            markdown: str,
            images: List[Image._Image],
            has_code: bool,
        ) -> None:
            self.name = name
            self.title = title
            self.post_metadata = post_metadata
            self.markdown = markdown
            self.images = images
            self.has_code = has_code

    def __new__(
        cls: Type["Post"], post_path: Path, image_base_url: Url
    ) -> "Post._Post":
        if Post.valid(post_path):
            content_path = post_path / CONTENT_FOLDER
            image_base_url = image_base_url / post_path.name / CONTENT_FOLDER

            unmodified_post_content = open(post_path / BLOG_TEXT, "r").read()

            images = []
            if content_path.is_dir():
                images = Post.find_images(
                    unmodified_post_content, content_path, image_base_url
                )

            modified_post_content = Post.rewrite_images(
                unmodified_post_content, str(image_base_url)
            )
            post_content_split = modified_post_content.split("\n")

            return Post._Post(
                post_path.name,
                post_content_split[0].lstrip("#").strip(),
                PostMetadata(
                    post_path / "metadata.json", Post.has_code(unmodified_post_content)
                ),
                Blog.MARKDOWN.render("\n".join(post_content_split[1:])),
                images,
                Post.has_code(unmodified_post_content),
            )
        else:
            print(
                "%sWARNING%s: Validation of '%s' failed!"
                % (WARNING_COLOR, ANSI_END, post_path)
            )

    def __repr__(self) -> str:
        return '<Post title="%s" name="%s" id=%s>' % (self.title, self.name, id(self))

    @staticmethod
    def valid(post_path: Path) -> bool:
        text_path = post_path / BLOG_TEXT
        metadata_path = post_path / BLOG_METADATA

        valid_text = False
        post_has_code = False

        if text_path.exists:
            split_text = open(text_path, "r").read().split("\n")
            if len(split_text) > 0:
                valid_text = bool(VALID_MARKDOWN.match(split_text[0]))
                # Required because code license is only necessary if post
                # contains code
                post_has_code = Post.has_code(open(text_path, "r").read())

        # Metadata can be valid, even if the text is invalid
        valid_metadata = metadata_path.exists() and PostMetadata.valid(
            metadata_path, post_has_code
        )

        return valid_text and valid_metadata

    @staticmethod
    def rewrite_images(post_content: str, image_base_url: str) -> str:
        for regex in IMAGE_REWRITE:
            post_content = regex.sub(
                "\g<1>%s/\g<2>\g<3>" % image_base_url, post_content
            )

        return post_content

    @staticmethod
    def find_images(
        post_content: str, content_path: Path, image_base_url: Url
    ) -> List[Image._Image]:
        images = [
            Image(
                content_path
                / Path(image_tuple[0] if image_tuple[0] else image_tuple[1]),
                image_base_url,
            )
            for image_tuple in FIND_IMAGE.findall(post_content)
        ]

        for image in images:
            if not image.path.is_file():
                print(
                    "%sWARNING%s: '%s' does not exist!"
                    % (WARNING_COLOR, ANSI_END, image.path)
                )

        return images

    @staticmethod
    def has_code(post_content: str) -> bool:
        return bool(HAS_CODE.search(post_content))


class Blog:
    class _HighlightRenderer(MistuneRenderer):
        def block_code(self, code: str, lang: Optional[str]) -> str:
            if not lang:
                return "\n<pre><code>%s</code></pre>\n" % mistune_escape(code)
            lexer = get_lexer_by_name(lang, stripall=True)
            formatter = html.HtmlFormatter()
            return highlight(code, lexer, formatter)

    class _FileSystemEventHandler(WatchdogFileSystemEventHandler):
        def __init__(self, method: Callable):
            self.method = method

        def on_any_event(self, event: Any):
            self.method()

    MARKDOWN = MistuneMarkdown(renderer=_HighlightRenderer())

    def __init__(
        self, path: Path, image_base_url: Url, rss_base_url: Url, rss_url: Url
    ) -> None:
        self.path = path
        self.image_base_url = image_base_url
        self.rss_base_url = rss_base_url
        self.rss_url = rss_url

        self.observer = Observer()
        self.observer.schedule(
            Blog._FileSystemEventHandler(self.__refresh_posts),
            str(path.absolute()),
            recursive=True,
        )
        self.observer.start()

        self._posts = []
        self._tags = {}
        self._rss = ""

        self.posts_lock = Lock()

        self.__refresh_posts()

    def find_post(self, name: str) -> Optional[Post._Post]:
        post = None

        self.posts_lock.acquire()
        for post_ in self._posts:
            if post_.name == name:
                post = post_
                break
        self.posts_lock.release()

        return post

    def find_posts(self, tag: str) -> List[Post._Post]:
        posts = []

        self.posts_lock.acquire()
        for post_ in self._posts:
            if tag in post_.post_metadata.tags:
                posts.append(post_)
        self.posts_lock.release()

        return posts

    @property
    def posts(self) -> List[Post._Post]:
        self.posts_lock.acquire()
        posts = self._posts[:]
        self.posts_lock.release()

        return self._posts

    @property
    def tags(self) -> Dict[str, List[Post._Post]]:
        self.posts_lock.acquire()
        tags = self._tags.copy()
        self.posts_lock.release()

        return self._tags

    @property
    def rss(self) -> str:
        self.posts_lock.acquire()
        rss = self._rss
        self.posts_lock.release()

        return rss

    def __refresh_posts(self) -> None:
        print("%sINFO%s: Refreshing!" % (EMPHASIS_COLOR, ANSI_END))

        posts = []
        tags = {}

        feed_items = []

        for folder in self.path.iterdir():
            if folder.is_dir() and Post.valid(folder):
                post = Post(folder, self.image_base_url)

                link = str(self.rss_base_url / post.name)

                if not post.post_metadata.hidden:
                    feed_items.append(
                        Item(
                            title=post.title,
                            link=link,
                            description=post.post_metadata.description,
                            author=post.post_metadata.author,
                            guid=Guid(link),
                            pubDate=post.post_metadata.date.datetime,
                        )
                    )

                    for tag in post.post_metadata.tags:
                        if not tag in tags:
                            tags[tag] = []
                        tags[tag].append(post)

                posts.append(post)

        feed = Feed(
            title="Philip Trauner",
            link=self.rss_url,
            description="",
            language="en-US",
            lastBuildDate=datetime.now(),
            items=feed_items,
        )

        self.posts_lock.acquire()

        self._posts = sorted(
            posts, key=lambda post: post.post_metadata.date.unix_date, reverse=True
        )
        self._tags = tags
        self._rss = feed.rss()

        self.posts_lock.release()
