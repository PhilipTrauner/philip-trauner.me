from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from .util import Url
from typing import List
from typing import Optional
from typing import Iterator

from pydantic import EmailStr
from pydantic import Field
from result import Result
from result import Ok
from result import Err
from rfeed import Serializable

from .license import TextLicenses
from .license import CodeLicenses
from .helper import ConfiguredBaseModel
from . import read_time
from .pattern import VALID_MARKDOWN
from .fault import post
from .constant import BLOG_TEXT
from .constant import BLOG_METADATA
from .constant import CONTENT_FOLDER
from .pattern import IMAGE_REWRITE
from .pattern import IMAGE_HREF
from .pattern import HEADING_PATTERN
from .markdown import render as render_markdown


"""
`BaseModel`s are used for classes that are sourced from disk
`dataclass` is used for everything else
"""


@dataclass(frozen=True)
class Image:
    url: Url


class ReadTimeHint(ConfiguredBaseModel):
    excluded_tags: List[str] = Field(default_factory=list)

    def into(self) -> read_time.Hint:
        return read_time.Hint(self.excluded_tags)


class Licensing(ConfiguredBaseModel):
    text: TextLicenses
    code: Optional[CodeLicenses]


class PostMetadata(ConfiguredBaseModel):
    description: str
    section: str
    tags: List[str]
    author: Optional[EmailStr]
    date: datetime

    license_: Licensing = Field(alias="license")
    read_time_hint: ReadTimeHint = Field(default=ReadTimeHint())

    hidden: bool = Field(default=False)


@dataclass(frozen=True)
class Post(Serializable):
    # Constructing the sentinel class is a failable operation (as disk I/O is performed)
    # while creating a post from an instantiated sentinel class will always succeed.
    @dataclass(frozen=True)
    class _ValidSentinel:
        path: Path
        content: str
        metadata: PostMetadata

    @dataclass(frozen=True)
    class _RenderedPost:
        html: str
        # The first image is used as the `og:image`
        images: List[Image]

        def __str__(self) -> str:
            return self.html

    name: str
    title: str
    content: str
    metadata: PostMetadata
    read_time: read_time.ReadTime

    @staticmethod
    def new(validated: "Post._ValidSentinel") -> "Post":
        # This is safe due to [ref:ensure_heading]
        title = validated.content.partition("\n")[0].lstrip("#").strip()

        return Post(
            validated.path.name,
            title,
            validated.content,
            validated.metadata,
            read_time.ReadTime(
                # Render the unmodified post content
                # Necessary to enable tag ignores for markdown constructs
                # (such as `<pre>` or `code`)
                Post.render_markdown(validated.content),
                validated.metadata.read_time_hint.into(),
            ),
        )

    @staticmethod
    def valid(path: Path) -> Result["Post._ValidSentinel", post.Fault]:
        text_path = path / BLOG_TEXT
        metadata_path = path / BLOG_METADATA

        if not text_path.exists():
            return Err(post.PathFault(text_path))

        try:
            content = open(text_path, "r").read()
        except IOError as e:
            return Err(post.IoFault(e))

        if not VALID_MARKDOWN.match(open(text_path, "r").readline()):
            return Err(post.MissingHeadingFault())  # [tag:ensure_heading]

        if not metadata_path.exists():
            return Err(post.MetadataMissingFault(metadata_path))

        metadata = PostMetadata.new(open(metadata_path, "r"))

        if isinstance(metadata, Ok):
            return Ok(Post._ValidSentinel(path, content, metadata.ok()))
        else:
            return Err(post.MetadataFault(metadata.err()))

    def render(
        self, base_static_url: Url, include_heading: bool = False
    ) -> _RenderedPost:
        base_post_static_url = base_static_url / self.name / CONTENT_FOLDER

        images = Post.find_images(self.content, base_post_static_url)

        modified_post_content = Post.rewrite_images(self.content, base_post_static_url)

        if not include_heading:
            modified_post_content = Post.strip_heading(modified_post_content)

        html = Post.render_markdown(modified_post_content)

        rendered = Post._RenderedPost(html, list(images))

        return rendered

    @staticmethod
    def render_markdown(post_content: str) -> str:
        return render_markdown(post_content)

    @staticmethod
    def rewrite_images(post_content: str, base_post_static_url: Url) -> str:
        for regex in IMAGE_REWRITE:
            post_content = regex.sub(
                r"\g<1>%s/\g<2>\g<3>" % str(base_post_static_url), post_content
            )

        return post_content

    @staticmethod
    def find_images(post_content: str, base_post_static_url: Url) -> Iterator[Image]:
        return (
            Image(
                base_post_static_url
                / (image[0] if image[0] else image[1])  # [ref:image_href_tuple]
            )
            for image in IMAGE_HREF.findall(post_content)
        )

    @staticmethod
    def strip_heading(post_content: str) -> str:
        # Only strip first occurence of pattern
        return HEADING_PATTERN.sub("", post_content, 1)

    def link(self, base_url: Url) -> Url:
        return base_url / self.name
