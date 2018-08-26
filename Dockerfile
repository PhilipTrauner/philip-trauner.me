# Use an official Python runtime as a parent image
FROM python:3.7-alpine as base

# For Poetry installation (Poetry is a build / runtime dependency)
FROM base as poetry

# Install Poetry dependencies
RUN apk --no-cache add curl
# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python3
# Create virtualenv location
RUN mkdir /virtualenvs
# Configure virtualenv location
RUN poetry config settings.virtualenvs.path "/virtualenvs"
# Clear root cache
RUN rm -rf /root/.cache
# Remove curl
RUN apk --no-cache del curl
# Clear apk cache
RUN rm -rf /var/cache/apk

# Install apk packages and compile missing tools
FROM base as base_build_packages

RUN apk --no-cache add git gcc g++ musl-dev make imagemagick cmake yarn nodejs
RUN git clone --depth=1 https://github.com/google/zopfli.git && \
	cd zopfli && mkdir build && cd build && cmake .. && make zopflipng && \
	mv zopflipng /usr/local/bin

FROM base_build_packages as js_build

COPY package.json yarn.lock /js/
WORKDIR js/
RUN yarn install

FROM poetry as python_build

RUN apk --no-cache add git musl-dev gcc make
COPY pyproject.toml pyproject.lock /python/
WORKDIR python/
RUN python3 -m poetry install --no-interaction

# For app build
FROM base_build_packages as app_build

ARG mode=prod
ENV MODE=$mode

COPY --from=js_build /js/node_modules /app/node_modules
COPY ./src/image /app/src/image
COPY ./src/script /app/src/script
COPY ./src/style /app/src/style
COPY ./utils /app/utils
COPY ./posts /app/posts
COPY package.json yarn.lock /app/
COPY Makefile /app
WORKDIR /app
RUN make build

FROM poetry

COPY --from=python_build /virtualenvs /virtualenvs
COPY --from=app_build /app/dist /app/dist
COPY --from=app_build /app/posts /app/posts
COPY ./src/template /app/src/template
COPY ./bridges/ /app/bridges
COPY ./app.py /app
COPY pyproject.toml /app
WORKDIR /app
# Make port 5000 available to the world outside this container
EXPOSE 5000
# Used to ensure that a config file has to be provided
ENV IN_DOCKER Yes
# Run app.py when the container launches
CMD ["poetry", "run", "python3", "app.py"]