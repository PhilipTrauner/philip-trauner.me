SRC_DIR = src
DIST_DIR = dist

STYLE := $(wildcard src/style/*.css)
STYLE := $(STYLE) src/style/github-markdown-processed.css src/style/github.css
STYLE := $(filter-out src/style/github-markdown-base.css, $(STYLE))
SCRIPT := $(wildcard src/script/*.js)
SOCIAL := $(wildcard src/image/social/*.png)
ICON := $(wildcard src/image/icon/*.png)

MINIFIED_STYLE := $(STYLE:$(SRC_DIR)%=$(DIST_DIR)%)
MINIFIED_SCRIPT := $(SCRIPT:$(SRC_DIR)%=$(DIST_DIR)%)

BLOG_IMAGES := $(wildcard blog/post/*/content/*.png)

.PHONY: build clean docker-build docker-push crunch

build: src/style/github.css src/style/github-markdown-processed.css \
	$(MINIFIED_STYLE) $(MINIFIED_SCRIPT) | dist

clean:
	rm -rf dist node_modules src/style/github-markdown-base.css \
		src/style/github-markdown-processed.css src/style/github.css

crunch:
	$(foreach image,$(BLOG_IMAGES),$(shell zopflipng -y "$(image)" "$(image)"))

$(DIST_DIR)/style/%.css: $(SRC_DIR)/style/%.css
	@mkdir -p $(dir $@)
	node_modules/uglifycss/uglifycss $< --output $@

$(DIST_DIR)/script/%.js: $(SRC_DIR)/script/%.js
	@mkdir -p $(dir $@)
	cp $< $@

node_modules: package.json yarn.lock
	yarn install

dist:
	mkdir -p dist

src/style/github-markdown-processed.css: src/style/github-markdown-base.css
	/usr/bin/env python3 utils/github_css_postprocess.py

src/style/github-markdown-base.css: node_modules
	node_modules/generate-github-markdown-css/cli.js > src/style/github-markdown-base.css

src/style/github.css: node_modules
	cp $(realpath node_modules/pygments-github-css/github.css) src/style/

docker-build: build
	docker build -t philiptrauner/homepage-app:latest -f docker/app/Dockerfile .
	docker build -t philiptrauner/homepage-web:latest -f docker/web/Dockerfile .

docker-push: docker-build
	docker push philiptrauner/homepage-app:latest
	docker push philiptrauner/homepage-web:latest
