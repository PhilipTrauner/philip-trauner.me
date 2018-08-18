.PHONY: build install run

build: node_modules static/github-markdown-base.css static/github.min.css
	node_modules/uglify-js/bin/uglifyjs static/home.js -o static/home.min.js
	node_modules/uglifycss/uglifycss static/base.css --output static/base.min.css
	node_modules/uglifycss/uglifycss static/home.css --output static/home.min.css
	node_modules/uglifycss/uglifycss static/blog-post.css --output static/blog-post.min.css	
	node_modules/uglifycss/uglifycss static/blog-tag.css --output static/blog-tag.min.css	
	python3 utils/github_css_postprocess.py
	node_modules/uglifycss/uglifycss static/github-markdown-processed.css --output static/github-markdown-processed.min.css
	convert static/twitter.png -resize 64x64 static/twitter.resized.png
	convert static/github.png -resize 64x64 static/github.resized.png
	convert static/spotify.png -resize 64x64 static/spotify.resized.png
	convert static/last-fm.png -resize 64x64 static/last-fm.resized.png

install: build
	poetry install

node_modules: 
	yarn install

static/github-markdown-base.css:
	node_modules/generate-github-markdown-css/cli.js > static/github-markdown-base.css

static/github.min.css:
	ln -sf $(realpath node_modules/pygments-github-css/github.min.css) static/

run: build
	poetry run python3 app.py
