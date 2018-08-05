from re import compile as re_compile

SYNTAX_HIGHLIGHTING = re_compile(r".markdown-body \.pl-\D.*\n([^}]*\n)*}")
FIRST_LAST_CHILDREN = re_compile(r".markdown-body>\*:(first|last)-child.*\n([^}]*\n)*}")
OCTICONS = re_compile(r"@font-face.*{\n([^}]*\n)*}")
FONT = re_compile(
    r"font-family: -apple-system,BlinkMacSystemFont,\"Segoe UI\",Helvetica,Arial,sans-serif,\"Apple Color Emoji\",\"Segoe UI Emoji\",\"Segoe UI Symbol\";"
)

APPLY_REGEX = [SYNTAX_HIGHLIGHTING, FIRST_LAST_CHILDREN, OCTICONS, FONT]

gh_md_content = open("static/github-markdown-base.css", "r").read()

for regex in APPLY_REGEX:
    gh_md_content = regex.sub("", gh_md_content)

open("static/github-markdown-processed.css", "w").write(gh_md_content)
