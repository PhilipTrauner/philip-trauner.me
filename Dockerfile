# Use an official Python runtime as a parent image
FROM python:3.6.6-alpine as base

# For Poetry installation
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

# For dependency build
FROM poetry as build

# Install build dependencies
RUN apk --no-cache add git gcc musl-dev make
# Grab dependency description
COPY pyproject.toml pyproject.lock /
# Install app dependencies
RUN python3 -m poetry install --no-interaction

# Use 
FROM poetry

# Grab built dependencies
COPY --from=build /virtualenvs /virtualenvs
# Copy the current directory contents into the container at /app
COPY . /app
WORKDIR /app
# Make port 5000 available to the world outside this container
EXPOSE 5000
# Used to ensure that a config file has to be provided
ENV IN_DOCKER Yes
# Run app.py when the container launches
CMD ["poetry", "run", "python3", "app.py"]