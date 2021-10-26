<img align="right" src="https://secure.gravatar.com/avatar/8325743a54507f02086dbe03d282c63c?s=500" width="100"></img>
# philip-trauner.me
[![Python 3.9](https://img.shields.io/badge/python-3.9-%233572A5.svg)](https://docs.python.org/3/whatsnew/3.9.html)

## Development

```
poetry install
poetry run python3 app.py
```

## Deployment

```sh
mkdir -p philip-trauner.me
cd philip-trauner.me
# Download files required for Docker-based deployment
wget https://raw.githubusercontent.com/PhilipTrauner/philip-trauner.me/main/docker-compose.yml
wget -O .env https://raw.githubusercontent.com/PhilipTrauner/philip-trauner.me/main/.env.template
# Inspect and edit `.env` file
# Clone `blog` repository
git clone https://github.com/PhilipTrauner/blog.git
```
