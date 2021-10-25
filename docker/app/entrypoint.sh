#!/bin/sh

set -e

RED="\033[0;31m"
COLOR_OFF="\033[0m"

function error {
	>&2 echo -e "${RED}${1}${COLOR_OFF}"
	exit ${2}
}

if [ ! -d "blog" ]; then
	error "Blog base directory does not exist ('/app/blog')" 1
fi

/app/.venv/bin/python3 app.py