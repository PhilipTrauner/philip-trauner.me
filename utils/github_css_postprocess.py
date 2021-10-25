#!/usr/bin/env python3
from re import compile as re_compile

SYNTAX_HIGHLIGHTING = re_compile(r".markdown-body \.pl-\D.*\n([^}]*\n)*}")
FIRST_LAST_CHILDREN = re_compile(r".markdown-body>\*:(first|last)-child.*\n([^}]*\n)*}")
OCTICONS = re_compile(r"@font-face.*{\n([^}]*\n)*}")
ROOT_SCOPE = re_compile(r"\.markdown-body :root {")

APPLY_REGEX = [SYNTAX_HIGHLIGHTING, FIRST_LAST_CHILDREN, OCTICONS]

gh_md_content = open("src/style/github-markdown-base.css", "r").read()

for regex in APPLY_REGEX:
    gh_md_content = regex.sub("", gh_md_content)

gh_md_content = ROOT_SCOPE.sub(":root {", gh_md_content)

open("src/style/github-markdown-processed.css", "w").write(gh_md_content)
