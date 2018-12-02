THIS := $(lastword $(MAKEFILE_LIST))

MODE ?= dev
VALID_MODES = dev prod

SRC_DIR = src
DIST_DIR = dist

STYLE  = $(wildcard src/style/*.css)
STYLE := $(filter-out src/style/github-markdown-base.css, $(STYLE))
SCRIPT = $(wildcard src/script/*.js)
SOCIAL = $(wildcard src/image/social/*.png)
ICON   = $(wildcard src/image/icon/*.png)

MINIFIED_STYLE  = $(STYLE:$(SRC_DIR)%=$(DIST_DIR)%)
MINIFIED_SCRIPT = $(SCRIPT:$(SRC_DIR)%=$(DIST_DIR)%)
MINIFIED_SOCIAL = $(SOCIAL:$(SRC_DIR)%=$(DIST_DIR)%)
MINIFIED_ICON   = $(ICON:$(SRC_DIR)%=$(DIST_DIR)%)

BLOG_IMAGES = $(wildcard blog/post/*/content/*.png)

.PHONY: build start install clean watch validate-build-type docker-build

build: validate-mode node_modules src/style/github-markdown-processed.css \
	src/style/github.css dist $(MINIFIED_STYLE) $(MINIFIED_SCRIPT) \
	$(MINIFIED_SOCIAL) $(MINIFIED_ICON) $(BLOG_IMAGES) optimize

start: build 
	poetry run python3 app.py

clean:
	rm -rf dist node_modules

install: pyproject.toml pyproject.lock
	poetry install

watch: 
	poetry run python3 app.py &
	fswatch -ro $(SRC_DIR) --event=Updated | xargs -n1 -I{} make build

optimize: $(BLOG_IMAGES)
ifeq ($(MODE),prod)	
	for image in $(BLOG_IMAGES) ; do \
		zopflipng -y $$image $$image ; \
		touch $$image ; \
	done
endif	

validate-mode:
ifeq ($(filter $(MODE),$(VALID_MODES)),)
	$(info Invalid mode '$(MODE)' (Valid: $(shell echo $(VALID_MODES) | sed "s/ /, /g")))
	@exit 1
endif

$(DIST_DIR)/style/%.css: $(SRC_DIR)/style/%.css
	@mkdir -p $(dir $@)
	node_modules/uglifycss/uglifycss $< --output $@

$(DIST_DIR)/script/%.js: $(SRC_DIR)/script/%.js
	@mkdir -p $(dir $@)
	node_modules/uglify-js/bin/uglifyjs $< -o $@  

$(DIST_DIR)/image/social/%.png: $(SRC_DIR)/image/social/%.png
	@mkdir -p $(dir $@)
ifeq ($(MODE),prod)
	convert $< -resize 64x64 $@
	zopflipng -y -m $@ $@
else
	cp $< $@
endif

$(DIST_DIR)/image/icon/%.png: $(SRC_DIR)/image/icon/%.png
	@mkdir -p $(dir $@)
	cp $< $@
ifeq ($(MODE),prod)
	zopflipng -y -m $@ $@
endif

node_modules: package.json yarn.lock
	yarn install

dist:
	mkdir -p dist

src/style/github-markdown-processed.css: src/style/github-markdown-base.css
	/usr/bin/env python3 utils/github_css_postprocess.py

src/style/github-markdown-base.css:
	node_modules/generate-github-markdown-css/cli.js > src/style/github-markdown-base.css

src/style/github.css:
	ln -sf $(realpath node_modules/pygments-github-css/github.css) src/style/


docker-build: build
	docker build -t philiptrauner/philip-trauner.me:prod .