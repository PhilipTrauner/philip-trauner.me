FROM python:3.14-alpine AS build

RUN apk --no-cache add git musl-dev libffi-dev openssl-dev gcc make g++

RUN pip3 --no-cache-dir install --upgrade pip poetry

COPY pyproject.toml poetry.lock ./

RUN set -eux; \
	poetry config virtualenvs.in-project true; \
	python3 -m poetry install --no-interaction --only main; \
	rm -rf .venv/src;

FROM python:3.14-alpine
WORKDIR /app

COPY --from=build .venv/ .venv/

COPY bridges ./bridges
COPY docker ./docker
COPY dist ./dist
COPY template ./template
COPY public ./public
COPY app.py ./

CMD ["./docker/entrypoint.sh"]
