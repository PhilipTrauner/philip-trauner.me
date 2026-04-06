#!/usr/bin/env python3
from re import MULTILINE
from re import compile as re_compile
from sys import stderr

SYNTAX_HIGHLIGHTING = re_compile(r"\.markdown-body \.pl-\D.*\n([^}]*\n)*}")
FIRST_LAST_CHILDREN = re_compile(r".*:(first|last)-child.*\n([^}]*\n)*}")
COLOR_SCHEME_DARK = re_compile(
    r"@media \(prefers-color-scheme: dark\)[^{]*{(?:[^{}]*|{[^{}]*})*}"
)

APPLY_REGEX = [SYNTAX_HIGHLIGHTING, FIRST_LAST_CHILDREN, COLOR_SCHEME_DARK]

gh_md_content = open("src/style/github-markdown-base.css", "r").read()

for regex in APPLY_REGEX:
    gh_md_content = regex.sub("", gh_md_content)


# promote light color scheme
COLOR_SCHEME_LIGHT = re_compile(
    r"@media \(prefers-color-scheme: light\)[^{]*{(?P<nested>(?:[^{}]*|{[^{}]*\})*)}",
)

# extract definitions nested in light color scheme media query
match = COLOR_SCHEME_LIGHT.search(gh_md_content)
if match is None:
    print("[!] could not find light color scheme definition", file=stderr)
    exit(1)

# remove light media query
gh_md_content = COLOR_SCHEME_LIGHT.sub("", gh_md_content)


# add nested definitions back
gh_md_content += re_compile(r", \[data-theme=\"light\"\]").sub(
    "", match.group("nested")
)

open("src/style/github-markdown-processed.css", "w").write(gh_md_content)
