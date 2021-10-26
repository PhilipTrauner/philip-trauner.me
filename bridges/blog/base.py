from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any
from typing import Callable

from result import Ok
from rfeed import Feed
from watchdog.events import FileSystemEventHandler as WatchdogFileSystemEventHandler
from watchdog.observers import Observer

from .util import info
from .util import Url
from .util import warning
from bridges.blog.container import Post
from bridges.blog.rss import build_feed
from bridges.blog.rss import FeedMetadata


class RwLock:
    def __init__(self) -> None:
        self._count = 0
        self._counter_lock = Lock()
        self._write_lock = Lock()

    def read_acquire(self) -> None:
        self._counter_lock.acquire()
        self._count += 1

        if self._count == 1:
            self._write_lock.acquire()

        self._counter_lock.release()

    def read_release(self) -> None:
        self._counter_lock.acquire()
        self._count -= 1

        if self._count == 0:
            self._write_lock.release()

        self._counter_lock.release()

    def write_acquire(self) -> None:
        self._write_lock.acquire()

    def write_release(self) -> None:
        self._write_lock.release()


class Blog:
    class _FileSystemEventHandler(WatchdogFileSystemEventHandler):
        def __init__(self, method: Callable) -> None:
            self.method = method

        def on_any_event(self, event: Any):  # type: ignore
            self.method()

    def __init__(
        self,
        base_path: Path,
        base_static_url: Url,
        rss_title: str,
        rss_description: str,
        rss_language: str,
        rss_base_url: Url,
        rss_url: Url,
    ) -> None:
        self.base_path = base_path
        self.base_static_url = base_static_url
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

        self._posts: list[Post] = []
        self._tags: dict[str, list[Post]] = {}
        self._rss: str = ""

        self.lock = RwLock()

        self.__refresh()

        self.observer.start()

    def find_post(self, name: str) -> Post | None:
        post = None

        self.lock.read_acquire()
        for post_ in self._posts:
            if post_.name == name:
                post = post_
                break
        self.lock.read_release()

        return post

    def find_posts_by_tag(self, tag: str) -> list[Post]:
        posts = []

        self.lock.read_acquire()
        for post_ in self._posts:
            if tag in post_.metadata.tags:
                posts.append(post_)
        self.lock.read_release()

        return posts

    @property
    def posts(self) -> list[Post]:
        self.lock.read_acquire()
        posts = self._posts[:]
        self.lock.read_release()

        return posts

    @property
    def tags(self) -> dict[str, list[Post]]:
        self.lock.read_acquire()
        tags = self._tags.copy()
        self.lock.read_release()

        return tags

    @property
    def rss(self) -> str:
        self.lock.read_acquire()
        rss = self._rss
        self.lock.read_release()

        return rss

    def _build_feed(self, posts: list[Post]) -> Feed:
        return build_feed(
            posts,
            FeedMetadata(
                self.rss_title,
                self.rss_url,
                self.rss_description,
                self.rss_language,
                self.rss_base_url,
                self.base_static_url,
            ),
        )

    def __refresh(self) -> None:
        info("Refreshing!")

        posts: list[Post] = []
        tags: dict[str, list[Post]] = {}

        for folder in self.post_path.iterdir():
            if folder.is_dir():
                sentinel = Post.valid(folder)
                if isinstance(sentinel, Ok):
                    post = Post.new(sentinel.ok())

                    for tag in post.metadata.tags:
                        if tag not in tags:
                            tags[tag] = []
                        tags[tag].append(post)

                    posts.append(post)
                else:
                    warning(f"{str(folder)}: {sentinel.err().description}")

        # https://github.com/python/mypy/issues/9656
        sorted_posts = sorted(
            posts,
            key=lambda post: post.metadata.date.timestamp(),  # type: ignore
            reverse=True,
        )

        self.lock.write_acquire()

        self._posts = sorted_posts
        self._tags = tags
        self._rss = self._build_feed(sorted_posts).rss()

        self.lock.write_release()
