from re import compile as re_compile
from re import MULTILINE
from re import Pattern as RegexPattern
from typing import List


VALID_MARKDOWN = re_compile(r"^#.*$")
IMAGE_REWRITE: List[RegexPattern] = [
    re_compile(r"(<img.*src=\")([^\"]*)(.*)"),  # <img src="image.png" />
    re_compile(r"(!\[.*\]\()([^)]*)(\))"),  # ![](image.png)
]
HEADING_PATTERN = re_compile(r"^#\s*(.+)$", MULTILINE)

# Two capture groups:
# 1. Markdown style image embeds
# 2. HTML style image embeds
# >>> IMAGE_HREF.findall('![](image_1.png) <img src="image_2.png" />') [tag:image_href_tuple]
# [('image_1.png', ''), ('', 'image_2.png')]
IMAGE_HREF = re_compile(r"(?:!\[.*\]\(([^)]*)\))|(?:<img.*src=\"([^\"]*))")
# Includes blocks without language identifier
CODE_BLOCK = re_compile(r"```.*\n(((?:(?!```).)+\n)|\n)*```\n")

IMAGE = re_compile(r"(<.*img[^>]*>)|(!\[[^\]]*\]\([^)]*\))")
CAPTION = re_compile(r"<figcaption[^>]*>[^>]*>")
DEFAULT = re_compile(r".*")
