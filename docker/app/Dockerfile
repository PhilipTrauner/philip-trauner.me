FROM python:3.11-alpine as build

RUN apk --no-cache add git musl-dev libffi-dev openssl-dev gcc make g++

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

RUN pip3 --no-cache-dir install --upgrade pip poetry

COPY pyproject.toml poetry.lock ./

RUN set -eux; \
	poetry config virtualenvs.in-project true; \
	python3 -m poetry install --no-interaction --only main; \
	rm -rf .venv/src;

FROM python:3.11-alpine
WORKDIR /app

COPY --from=build .venv/ .venv/

COPY bridges ./bridges
COPY docker/app ./docker/app
COPY dist ./dist
COPY template ./template
COPY app.py ./

CMD ["./docker/app/entrypoint.sh"]
