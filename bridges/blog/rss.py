from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from typing import List
from xml.sax.saxutils import XMLGenerator  # nosec

from rfeed import Category
from rfeed import Extension
from rfeed import Feed
from rfeed import Guid
from rfeed import Item
from rfeed import Serializable

from .container import Post
from .util import encode_as_cdata
from .util import Url

# Threat model: Blog posts are trusted


@dataclass
class FeedMetadata:
    title: str
    link: Url
    description: str
    language: str

    base_url: Url
    base_image_url: Url


class PostWrapper(Serializable):
    def __init__(self, post: Post, base_image_url: Url):
        super().__init__()

        self.post = post
        self.base_image_url = base_image_url

    def publish(self, handler: XMLGenerator) -> None:
        Serializable.publish(self, handler)

        self._write_element(
            "content:encoded",
            encode_as_cdata(self.post.render(self.base_image_url, False).html),
            {},
        )


# Adds namespace for `<content:encoded>`
class ContentExtension(Extension):
    def get_namespace(self) -> Dict[str, str]:
        return {"xmlns:content": "http://purl.org/rss/1.0/modules/content/"}


def build_item(post: Post, base_url: Url, base_image_url: Url) -> Item:
    link = post.link(base_url)

    return Item(
        title=post.title,
        link=link,
        description=post.metadata.description,
        author=post.metadata.author,
        guid=Guid(link),
        pubDate=post.metadata.date,
        categories=[Category(tag) for tag in post.metadata.tags],
        enclosure=PostWrapper(post, base_image_url),
    )


def build_feed(posts: List[Post], feed_metadata: FeedMetadata) -> Feed:
    feed_items: List[Item] = []

    for post in posts:
        if not post.metadata.hidden:
            feed_items.append(
                build_item(post, feed_metadata.base_url, feed_metadata.base_image_url)
            )

    feed = Feed(
        title=feed_metadata.title,
        link=feed_metadata.link,
        description=feed_metadata.description,
        language=feed_metadata.language,
        lastBuildDate=datetime.now(),
        items=feed_items,
        extensions=[ContentExtension()],
    )
    feed.docs = None
    feed.generator = None

    return feed
