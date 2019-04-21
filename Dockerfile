FROM python:3.7.1-alpine3.8

COPY pyproject.toml poetry.lock /app/

RUN set -eux; \
	mkdir -p /var/virtualenvs; \
	cd /app; \
	apk --no-cache add --virtual build-dependencies git musl-dev gcc make; \
	pip3 install poetry; \
	poetry config settings.virtualenvs.path "/var/virtualenvs"; \
	python3 -m poetry install --no-interaction; \
	apk del build-dependencies; \
	find / -type d -name __pycache__ -prune -exec rm -rf '{}' \;; \
	rm -rf /usr/local/lib/python3.7/site-packages/*; \
	rm -rf /var/virtualenvs/philip-trauner.me-py3.7/lib/python3.7/site-packages/pip/; \
	rm -rf /var/virtualenvs/philip-trauner.me-py3.7/src/rfeed/.git;

COPY . /app/
WORKDIR /app

CMD ["./docker/entrypoint.sh"]