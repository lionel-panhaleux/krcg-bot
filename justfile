quality:
    ruff format --check .
    ruff check .

test: quality
    pytest -vvs

release:
    uv sync --dev
    uv build
    uv publish

update:
    uv sync --dev --upgrade

serve:
    source .env && krcg-bot

clean:
    rm -rf dist
    rm -rf .pytest_cache
    rm -rf .ruff_cache

default:
    @just --list 