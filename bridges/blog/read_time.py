from dataclasses import dataclass
from re import Pattern as RegexPattern
from typing import Dict
from typing import List
from typing import Optional

from bs4 import BeautifulSoup

from .pattern import CAPTION
from .pattern import DEFAULT
from .pattern import IMAGE
from .time import Time

WORDS_PER_MINUTE = 275


@dataclass
class Impact:
    per_occurrence: float
    per_line: float
    per_word: float


@dataclass(unsafe_hash=True)
class Pattern:
    regex: RegexPattern
    singular: str
    plural: str

    def label(self, count: int) -> str:
        return self.plural if count > 1 else self.singular


IMAGE_DESCRIPTION = Pattern(IMAGE, "Image", "Images")
CAPTION_DESCRIPTION = Pattern(CAPTION, "Caption", "Captions")
DEFAULT_DESCRIPTION = Pattern(DEFAULT, "Text", "Text")

IMPACT: Dict[Pattern, Impact] = {
    # (Per occurence, Per line, Per word)
    IMAGE_DESCRIPTION: Impact(8.0, 0.0, 0.0),
    CAPTION_DESCRIPTION: Impact(3.0, 0.0, 0.0),
    # https://blog.medium.com/read-time-and-you-bc2048ab620c
    DEFAULT_DESCRIPTION: Impact(0.0, 0.0, 1.0 / (WORDS_PER_MINUTE / 60.0)),
}

IGNORED_TAGS = ("details",)


@dataclass
class Hint:
    ignored_tags: List[str]


@dataclass
class BreakdownEntry:
    # Used to determine if plural or singular form of pattern description is used
    count: int
    time: Time


@dataclass(init=False)
class ReadTime:
    overall_time: Time
    word_count: int
    time_breakdown: Dict[Pattern, BreakdownEntry]

    def __init__(self, post_content: str, hint: Hint) -> None:
        overall_time = Time()
        time_breakdown: Dict[Pattern, BreakdownEntry] = {}

        # Content within excluded tags should be included in read time estimate
        stripped_post_content = ReadTime.strip_tags(post_content, hint.ignored_tags)

        words: Optional[int] = None

        for impact in IMPACT.keys():
            count = 0
            lines = 0
            words = 0

            for match in impact.regex.finditer(stripped_post_content):
                idx_1, idx_2 = match.span()
                text = stripped_post_content[idx_1:idx_2]

                count += 1

                # Don't include empty lines
                lines += len([line for line in text.split("\n") if line != ""])
                words += len(text.split(" "))

            time_breakdown[impact] = BreakdownEntry(
                count,
                Time.from_seconds(
                    IMPACT[impact].per_occurrence * count
                    + IMPACT[impact].per_line * lines
                    + IMPACT[impact].per_word * words
                ),
            )

            overall_time += time_breakdown[impact].time

            stripped_post_content = impact.regex.sub("", stripped_post_content)

        self.overall_time = overall_time
        self.word_count = words or 0
        self.time_breakdown = time_breakdown

    @property
    def formatted_time_breakdown(self) -> Dict[str, Optional[str]]:
        return {
            impact.singular
            if self.time_breakdown[impact].count <= 1
            else impact.plural: self.time_breakdown[impact].time.format_()
            for impact in self.time_breakdown
            if self.time_breakdown[impact].count > 0
        }

    @staticmethod
    def strip_tags(post_content: str, ignored_tags: List[str]) -> str:
        bs = BeautifulSoup(post_content, features="html5lib")
        for tag in ignored_tags:
            for bs_tag in bs.find_all(tag):
                bs_tag.decompose()

        return str(bs)
