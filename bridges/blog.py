from __future__ import annotations

from pathlib import Path
from threading import Lock
from json import loads as json_loads
from json.decoder import JSONDecodeError
from datetime import datetime
from re import compile as re_compile
from re import MULTILINE
from datetime import time as _time
from typing import Callable, List, Optional, Tuple, Type, Dict, Any, Union, Iterable
from enum import Enum
from functools import partial
from dataclasses import dataclass


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler as WatchdogFileSystemEventHandler

from markdown import Markdown as BaseMarkdown

from urlpath import URL as Url

from rfeed import Feed, Item, Guid, Category

from voluptuous import Required, Schema, Range, All, Optional, MultipleInvalid
from voluptuous import Any as VolAny

from util import (
    safe_execute,
    capture_trace,
    warning,
    info,
    all_match_condition,
    index_range_from_pair,
    traverse_collection,
)

REGEX_TYPE = type(re_compile(""))

LICENSE_VERSION = "4.0"

LICENSE_BASE_URL = "https://creativecommons.org/licenses/"
LICENSE_END_URL = "%s/" % LICENSE_VERSION

LICENSE_IMAGE_BASE_URL = "https://licensebuttons.net/i/l/"
LICENSE_IMAGE_END_URL = "transparent/00/00/00/88x31.png"

VALID_MARKDOWN = re_compile(r"^#.*$")
IMAGE_REWRITE: List[REGEX_TYPE] = [
    re_compile(r"(<img.*src=\")([^\"]*)(.*)"),  # <img src="image.png" />
    re_compile(r"(!\[.*\]\()([^)]*)(\))"),  # ![](image.png)
]

# Excludes blocks without language identifier
HAS_CODE = re_compile(r"```\w+\n")
IMAGE_HREF = re_compile(r"(?:!\[.*\]\(([^)]*)\))|(?:<img.*src=\"([^\"]*))")
# Includes blocks without language identifier
CODE_BLOCK = re_compile(r"```.*\n(((?:(?!```).)+\n)|\n)*```\n")
IMAGE = re_compile(r"(<.*img[^>]*>)|(!\[[^\]]*\]\([^)]*\))")
CAPTION = re_compile(r"<figcaption[^>]*>[^>]*>")
DEFAULT = re_compile(r".*")

WORDS_PER_MINUTE = 275

READ_TIME_IMPACT: Dict[REGEX_TYPE, Tuple[float, float, float]] = {
    # (Per occurence, Per line, Per word)
    IMAGE: (8.0, 0.0, 0.0),
    # There does not appear to be any code reading time statistics
    # (which makes total sense), so this figure is completely made up
    CODE_BLOCK: (0.0, 3.0, 0.0),
    CAPTION: (3.0, 0.0, 0.0),
    # https://blog.medium.com/read-time-and-you-bc2048ab620c
    DEFAULT: (0.0, 0.0, 1.0 / (WORDS_PER_MINUTE / 60.0)),
}

READ_TIME_IMPACT_NAME: Dict[REGEX_TYPE, Tuple[str, str]] = {
    IMAGE: ("Image", "Images"),
    CODE_BLOCK: ("Code Block", "Code Blocks"),
    CAPTION: ("Caption", "Captions"),
    DEFAULT: ("Text", "Text"),
}

CONTENT_FOLDER = "content"
BLOG_METADATA = "metadata.json"
BLOG_TEXT = "text.md"


def _cc_license_urls(license_string: str) -> Tuple[Url, Url]:
    return (
        Url(LICENSE_BASE_URL) / license_string / LICENSE_END_URL,
        Url(LICENSE_IMAGE_BASE_URL) / license_string / LICENSE_IMAGE_END_URL,
    )


class Markdown(BaseMarkdown):
    def render(self, *args, **kwargs):
        return self.reset().convert(*args, **kwargs)


@dataclass
class Validator:
    callable_: Callable
    error: str = ""


@dataclass
class ValidationResult:
    success: bool
    error: Optional[str] = None
    exception: Optional[Any] = None


def validate(validators: List[Validator]) -> Tuple[bool, str]:
    for validator in validators:
        try:
            if not validator.callable_():
                return ValidationResult(False, validator.error)
        except Exception as e:
            capture_trace()
            return ValidationResult(False, exception=e)
    return ValidationResult(True)


@dataclass
class License:
    name: str
    description_url: Url


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


@dataclass
class Author:
    name: str
    email: str

    def __eq__(self, other):
        return type(other) is Author and other.__dict__ == self.__dict__

    def __repr__(self):
        return "%s <%s>" % (self.name, self.email)

    def __str__(self):
        return self.name


class Date:
    def __init__(self, unix_date: int) -> None:
        self.unix_date = unix_date
        self.datetime = datetime.fromtimestamp(unix_date)
        self.pretty_date = self.datetime.strftime("%B %d, %Y")
        self.iso_date = self.datetime.strftime("%Y-%m-%d %H:%M:%S")


# Wrapper class around datetime.time
class Time:
    class Format(Enum):
        BLOG = 1

    def __init__(self, *args, **kwargs):
        self._time = _time(*args, **kwargs)

    @staticmethod
    def from_seconds(number: Union[int, float]):
        hours = divmod(number, 3600)
        minutes = divmod(hours[1], 60)
        seconds = minutes[1]
        microseconds = (
            ((number - int(number)) * 1000000) if type(number) is float else 0
        )

        return Time(int(hours[0]), int(minutes[0]), int(seconds), int(microseconds))

    def format_(self, format_=Format.BLOG) -> Union[str, None]:
        def round_minute(minute, second):
            return minute if second < 30 else minute + 1

        def round_hour(hour, minute):
            return round_minute(hour, minute)

        if format_ == Time.Format.BLOG:
            if self._time.minute == 0 and self._time.hour == 0:
                return "%i %s" % (
                    self._time.second,
                    "Second" if self._time.second == 1 else "Seconds",
                )
            elif self._time.hour == 0 and self._time.minute > 0:
                minute = round_minute(self._time.minute, self._time.second)
                return "%i %s" % (minute, "Minute" if minute == 1 else "Minutes")
            elif self._time.hours > 0:
                hour = round_hour(self._time.hour, self._time.minute)
                minute = round_minute(self._time.minute, self._time.second)
                return "%i %s %i %s" % (
                    hour,
                    "Hour" if hour == 1 else "Hours",
                    minute,
                    "Minute" if minute == 1 else "Minutes",
                )
            return "∞ Millennia"
        return None

    def __getattr__(self, attr):
        if hasattr(self._time, attr):
            return getattr(self._time, attr)
        raise AttributeError

    def __add__(self, other):
        if type(other) in (Time, _time):
            # The default constructor of datetime.time enforces ranges for
            # minutes, seconds, and milliseconds
            return Time.from_seconds(
                (self._time.hour + other.hour) * 3600
                + (self._time.minute + other.minute) * 60
                + (self._time.second + other.second)
                + (self._time.microsecond + other.microsecond) / 1000000
            )
        return NotImplemented

    def __repr__(self):
        return self.format_()

    def __str__(self):
        return self.format_()


class ReadTime:
    def __init__(
        self,
        time_breakdown: Dict[REGEX_TYPE, Tuple[int, Time]],
        overall_time: Time,
        word_count: int,
    ) -> None:
        self.time_breakdown: Dict[REGEX_TYPE, Tuple[int, Time]] = time_breakdown
        self.overall_time = overall_time
        self.word_count = word_count

        self.pretty_time_breakdown = {
            READ_TIME_IMPACT_NAME[regex][0]
            if time_breakdown[regex][0] <= 1
            else READ_TIME_IMPACT_NAME[regex][1]: time_breakdown[regex][1].format_(
                Time.Format.BLOG
            )
            for regex in time_breakdown
            if time_breakdown[regex][0] != 0
        }
        self.pretty_overall_time = self.overall_time.format_(Time.Format.BLOG)


class Image:
    @dataclass
    class _Image:
        path: str
        url: Url

    def __new__(cls: Type[Image], path: Path, image_base_url: Url):
        return Image._Image(path.absolute(), image_base_url / path.name)


class PostMetadata:
    TEXT_LICENSE = {"text": VolAny(*VALID_TEXT_LICENSE_STRINGS)}
    CODE_LICENSE = {"code": VolAny(*VALID_CODE_LICENSE_STRINGS)}
    BASE_VALIDATION_SCHEMA = {
        "description": str,
        "section": str,
        "author": str,
        "date": All(int, Range(min=1)),
        "tags": [str],
        Optional("hidden", default=False): bool,
    }
    VALIDATION_SCHEMA_WITHOUT_CODE = Schema(
        {**BASE_VALIDATION_SCHEMA, "license": {**TEXT_LICENSE}}, required=True
    )
    VALIDATION_SCHEMA_WITH_CODE = Schema(
        {**BASE_VALIDATION_SCHEMA, "license": {**TEXT_LICENSE, **CODE_LICENSE}},
        required=True,
    )

    @dataclass
    class _PostMetadata:
        date: Date
        tags: List[str]
        text_license: TextLicense
        code_license: Optional[CodeLicense]
        description: str
        section: str
        author: str
        hidden: bool

    def __new__(
        cls: Type[PostMetadata], metadata_path: Path, post_has_code: bool
    ) -> Optional[PostMetadata._PostMetadata]:

        try:
            metadata_dict = (
                PostMetadata.VALIDATION_SCHEMA_WITH_CODE
                if post_has_code
                else PostMetadata.VALIDATION_SCHEMA_WITHOUT_CODE
            )(json_loads(open(metadata_path, "r").read()))
        except MultipleInvalid as e:
            warning("Validation of '%s' failed: %s" % (metadata_path, str(e)))
            return None

        return PostMetadata._PostMetadata(
            Date(metadata_dict["date"]),
            metadata_dict["tags"],
            TEXT_LICENSES[metadata_dict["license"]["text"]],
            CODE_LICENSES[metadata_dict["license"]["code"]] if post_has_code else None,
            metadata_dict["description"],
            metadata_dict["section"],
            metadata_dict["author"],
            metadata_dict.get("hidden", False),
        )

    @staticmethod
    def valid(metadata_path: Path, post_has_code: bool) -> bool:
        try:
            (
                PostMetadata.VALIDATION_SCHEMA_WITH_CODE
                if post_has_code
                else PostMetadata.VALIDATION_SCHEMA_WITHOUT_CODE
            )(json_loads(open(metadata_path, "r").read()))
        except MultipleInvalid as e:
            warning("Validation of '%s' failed: %s" % (metadata_path, str(e)))
            return False

        return True


class Post:
    @dataclass
    class _Post:
        name: str
        title: str
        post_metadata: PostMetadata._PostMetadata
        markdown: str
        images: List[Image._Image]
        has_code: bool
        read_time: ReadTime

    def __new__(
        cls: Type[Post], post_path: Path, image_base_url: Url, validated: bool = False
    ) -> Optional[Post._Post]:
        if validated or Post.valid(post_path):
            content_path = post_path / CONTENT_FOLDER
            image_base_url = image_base_url / post_path.name / CONTENT_FOLDER

            unmodified_post_content = open(post_path / BLOG_TEXT, "r").read()

            images: List[Image] = []
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
                    post_path / BLOG_METADATA, Post.has_code(unmodified_post_content)
                ),
                Blog.MARKDOWN.render("\n".join(post_content_split[1:])),
                images,
                Post.has_code(unmodified_post_content),
                ReadTime(*Post.read_time(unmodified_post_content)),
            )
        else:
            return None

    def __repr__(self) -> str:
        return '<Post title="%s" name="%s" id=%s>' % (self.title, self.name, id(self))

    @staticmethod
    def valid(post_path: Path) -> bool:
        text_path = post_path / BLOG_TEXT
        metadata_path = post_path / BLOG_METADATA

        valid_text = False
        post_has_code = False

        validation_result = validate(
            [
                Validator(
                    partial(lambda text_path: text_path.exists, text_path),
                    "path to post does not exist",
                ),
                Validator(
                    partial(
                        lambda text_path: bool(
                            VALID_MARKDOWN.match(
                                open(text_path, "r").read().split("\n")[0]
                            )
                        ),
                        text_path,
                    ),
                    "post has no heading",
                ),
            ]
        )

        if validation_result.success:
            valid_text = True
            post_has_code = Post.has_code(open(text_path, "r").read())

            # Metadata can be valid, even if the text is invalid
            valid_metadata = metadata_path.exists() and PostMetadata.valid(
                metadata_path, post_has_code
            )
        else:
            warning(
                "Validation of '%s' failed: %s" % (post_path, validation_result.error)
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
            for image_tuple in IMAGE_HREF.findall(post_content)
        ]

        for image in images:
            if not image.path.is_file():
                warning("'%s' does not exist!" % (image.path))

        return images

    @staticmethod
    def has_code(post_content: str) -> bool:
        return bool(HAS_CODE.search(post_content))

    @staticmethod
    def read_time(post_content: str) -> Tuple[Dict[REGEX_TYPE, Tuple[int, Time]], Time]:
        overall_time = Time()
        time_breakdown = {}

        # 3.7: Dictionary order is guaranteed to be insertion order
        for regex in READ_TIME_IMPACT.keys():
            count = 0
            lines = 0
            words = 0

            for match in regex.finditer(post_content):
                text = index_range_from_pair(post_content, match.span())

                count += 1
                # Don't include empty lines
                lines += len([line for line in text.split("\n") if line != ""])
                words += len(text.split(" "))

            time_breakdown[regex] = (
                count,
                Time.from_seconds(
                    READ_TIME_IMPACT[regex][0] * count
                    + READ_TIME_IMPACT[regex][1] * lines
                    + READ_TIME_IMPACT[regex][2] * words
                ),
            )

            overall_time += time_breakdown[regex][1]

            post_content = regex.sub("", post_content)

        return time_breakdown, overall_time, words


class Blog:
    class _FileSystemEventHandler(WatchdogFileSystemEventHandler):
        def __init__(self, method: Callable) -> None:
            self.method = method

        def on_any_event(self, event: Any):
            self.method()

    MARKDOWN = Markdown(
        extensions=[
            "footnotes",
            "nl2br",
            "codehilite",
            "fenced_code",
            "pymdownx.tilde",
        ],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,
                "linenums": False,
            }
        },
        output_format="html5",
    )

    def __init__(
        self,
        base_path: Path,
        image_base_url: Url,
        rss_title: str,
        rss_description: str,
        rss_language: str,
        rss_base_url: Url,
        rss_url: Url,
    ) -> None:
        self.base_path = base_path
        self.image_base_url = image_base_url
        self.rss_title = rss_title
        self.rss_description = rss_description
        self.rss_language = rss_language
        self.rss_base_url = rss_base_url
        self.rss_url = rss_url

        self.post_path = base_path / "post"

        self.observer = Observer()
        self.observer.schedule(
            Blog._FileSystemEventHandler(self.__refresh),
            str(self.post_path.absolute()),
            recursive=True,
        )

        self._posts: List[Post] = []
        self._tags: Dict[str, List[Post]] = {}
        self._authors: Dict[Author, List[Post]] = {}
        self._rss: str = ""

        self.lock = Lock()

        self.__refresh()

        self.observer.start()

    def find_post(self, name: str) -> Optional[Post._Post]:
        post = None

        self.lock.acquire()
        for post_ in self._posts:
            if post_.name == name:
                post = post_
                break
        self.lock.release()

        return post

    def find_posts_by_tag(self, tag: str) -> List[Post._Post]:
        posts = []

        self.lock.acquire()
        for post_ in self._posts:
            if tag in post_.post_metadata.tags:
                posts.append(post_)
        self.lock.release()

        return posts

    @property
    def posts(self) -> List[Post._Post]:
        self.lock.acquire()
        posts = self._posts[:]
        self.lock.release()

        return posts

    @property
    def tags(self) -> Dict[str, List[Post._Post]]:
        self.lock.acquire()
        tags = self._tags.copy()
        self.lock.release()

        return tags

    @property
    def authors(self) -> Dict[str, List[Post._Post]]:
        self.lock.acquire()
        authors = self._authors.copy()
        self.lock.release()

        return authors

    @property
    def rss(self) -> str:
        self.lock.acquire()
        rss = self._rss
        self.lock.release()

        return rss

    def __refresh(self) -> None:
        info("Refreshing!")

        posts = []
        tags = {}
        authors = {}

        feed_items = []

        for folder in self.post_path.iterdir():
            if folder.is_dir():
                post = Post(folder, self.image_base_url)

                # To-Do: Use in-line assignment once Python 3.8 rolls around
                if post is not None:
                    link = str(self.rss_base_url / post.name)

                    if not post.post_metadata.hidden:
                        feed_items.append(
                            Item(
                                title=post.title,
                                link=link,
                                description=post.post_metadata.description,
                                # author=post.post_metadata.author.email,
                                guid=Guid(link),
                                pubDate=post.post_metadata.date.datetime,
                                categories=[
                                    Category(tag) for tag in post.post_metadata.tags
                                ],
                            )
                        )

                        for tag in post.post_metadata.tags:
                            if not tag in tags:
                                tags[tag] = []
                            tags[tag].append(post)

                        author = post.post_metadata.author
                        if not author in authors:
                            authors[author] = []
                        authors[author].append(post)

                    posts.append(post)

        feed = Feed(
            title=self.rss_title,
            link=self.rss_url,
            description=self.rss_description,
            language=self.rss_language,
            lastBuildDate=datetime.now(),
            items=feed_items,
        )

        self.lock.acquire()

        self._posts = sorted(
            posts, key=lambda post: post.post_metadata.date.unix_date, reverse=True
        )
        self._tags = tags
        self._authors = authors
        self._rss = feed.rss()

        self.lock.release()