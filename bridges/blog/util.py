from typing import cast
from typing import Union

from html import escape as html_escape
from furl import furl as Furl

WARNING_COLOR = "\033[33m"
EMPHASIS_COLOR = "\033[35m"
ANSI_END = "\033[0m"

CDATA_END = "]]>"
ESCAPED_CDATA_END = html_escape(CDATA_END)


def uncapitalize(text: str) -> str:
    if len(text) > 0:
        return text[0].lower() + text[1:]
    return text


def warning(text: str) -> None:
    print("%sWARN%s: %s" % (WARNING_COLOR, ANSI_END, text))


def info(text: str) -> None:
    print("%sINFO%s: %s" % (EMPHASIS_COLOR, ANSI_END, text))


def encode_as_cdata(text: str) -> str:
    # https://stackoverflow.com/a/223782/4739690
    return f"<![CDATA[{text.replace(CDATA_END, ESCAPED_CDATA_END)}]]>"


class Url(Furl):
    def __str__(self) -> str:
        return cast(str, self.tostr())

    # Enforce type signature of divide operations
    def __truediv__(self, path: Union["Url", str]) -> "Url":
        return cast(Url, super().__truediv__(path))
