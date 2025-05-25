help:
    @just --list

# Runs all tests
test:
    uv run pytest

# Runs all lints (might apply fixes)
lint:
    uv run ruff check --fix
    uv run mypy .

# Runs formatting
fmt:
    uv run ruff format

# docker compose down
down:
    docker compose down

# remove config
rm-config:
    sudo git clean -dfX config


# docker compose up
up:
    docker compose up --remove-orphans

# start clean docker compose up
nup:
    @just down
    @just rm-config
    @just up

# Open home assistant in browser
ha:
    python3 -m webbrowser "http://localhost:8123"

cbuild:
    rm config/www/custom-apex-card.js
    cd custom_cards && npm run build && cp --remove-destination dist/*.js ../config/www/
