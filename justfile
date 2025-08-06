quality:
    uv run ruff format --check .
    uv run ruff check .

test: quality
    uv run pytest -vvs

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
