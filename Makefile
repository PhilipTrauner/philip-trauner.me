.PHONY: setup

build: setup uglify

setup:
	pipenv install
	npm install
	git lfs pull

uglify:
	npm run build
