from functools import lru_cache
from threading import Condition
from threading import Event
from threading import Lock
from threading import Thread
from typing import List

from markdown import Markdown

from .util import warning


def build_markdown() -> Markdown:
    return Markdown(
        extensions=[
            "admonition",
            "codehilite",
            "fenced_code",
            "footnotes",
            "nl2br",
            "pymdownx.keys",
            "pymdownx.tasklist",
            "pymdownx.tilde",
            "tables",
        ],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,  # type: ignore
                "linenums": False,  # type: ignore
            }
        },
        output_format="html",
    )


LRU_SIZE = 64
# `Markdown.reset()` doesn't sufficiently evict all leftovers of previous render
POOL_SIZE = 32
POOL_PRESSURE = POOL_SIZE / 4
POOL: List[Markdown] = [build_markdown() for _ in range(POOL_SIZE)]
POOL_BITMAP: List[bool] = [True for _ in range(POOL_SIZE)]
POOL_BITMAP_LOCK = Lock()
POOL_EXHAUSTED_CONDITION = Condition()
HYDRATION_EVENT = Event()


def hydrate() -> None:
    while True:
        HYDRATION_EVENT.wait()
        HYDRATION_EVENT.clear()

        POOL_BITMAP_LOCK.acquire()
        required_instance_count = POOL_BITMAP.count(False)
        POOL_BITMAP_LOCK.release()

        if required_instance_count >= POOL_PRESSURE:
            instances = [build_markdown() for _ in range(required_instance_count)]

            POOL_BITMAP_LOCK.acquire()

            for idx, bit in enumerate(POOL_BITMAP):
                if not bit:
                    try:
                        instance = instances.pop(0)
                    except IndexError:
                        break
                    else:
                        POOL[idx] = instance
                        POOL_BITMAP[idx] = True

            POOL_BITMAP_LOCK.release()
            with POOL_EXHAUSTED_CONDITION:
                POOL_EXHAUSTED_CONDITION.notify()


@lru_cache(maxsize=LRU_SIZE)
def render(text: str) -> str:
    POOL_BITMAP_LOCK.acquire()
    try:
        idx = POOL_BITMAP.index(True)
    except ValueError:
        warning(
            "Render pool too small, consider incrementing `POOL_SIZE` or "
            "decreasing `POOL_PRESSURE`"
        )

        # Ensure that at least one instance is avaliable
        POOL_BITMAP_LOCK.release()
        with POOL_EXHAUSTED_CONDITION:
            POOL_EXHAUSTED_CONDITION.wait()
            POOL_BITMAP_LOCK.acquire()

        idx = POOL_BITMAP.index(True)
    finally:
        # `.index` is guaranteed to only ever throw `ValueError`, therefor this
        # is safe

        # Mark instance as used
        POOL_BITMAP[idx] = False  # type: ignore
        POOL_BITMAP_LOCK.release()
        # Request creation of new instances
        HYDRATION_EVENT.set()

    instance = POOL[idx]  # type: ignore

    return instance.convert(text)


t = Thread(target=hydrate)
t.daemon = True
t.start()

__all__ = ["render"]
