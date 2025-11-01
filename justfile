# Default recipe to list all available recipes
default:
    @just --list

# Lint, format and type check code
quality:
    uv run ruff format --check
    uv run ruff check
    uv run mypy krcg_bot

# Run tests & quality
test: quality
    uv run pytest -vvs

# Update dependencies
update:
    uv sync --dev --upgrade

# Serve the bot locally
serve:
    source .env && krcg-bot

# Clean build artifacts
clean-build:
    @echo "🧹 Cleaning build artifacts..."
    rm -rf build dist
    @echo "✅ Cleaned!"

# Clean build and cache artifacts
clean: clean-build
    @echo "🧹 Cleaning cache..."
    rm -rf .pytest_cache .mypy_cache .ruff_cache
    @echo "✅ Cleaned!"

# Ensure we're on master branch and working tree is clean
check:
    @echo "🔍 Checking release prerequisites..."
    @if [[ "$(git branch --show-current)" != "master" ]]; then echo "❌ Not on master branch"; exit 1; fi
    @if [[ -n "$(git status --porcelain)" ]]; then echo "❌ Working directory is dirty"; exit 1; fi
    @echo "✅ Release checks passed!"

# Build the package
build:
    @echo "🔨 Building package..."
    uv build
    @echo "✅ Package built!"

# Bump the version (level: minor | major)
bump level="minor": check
    #!/usr/bin/env bash
    set -euo pipefail
    uv version --bump "{{ level }}"
    VERSION="$(uv version --short)"
    echo "📝 Committing version ${VERSION}..."
    git add pyproject.toml
    git commit -m "Release ${VERSION}" && git tag "v${VERSION}"
    echo "📤 Pushing to remote..."
    git push origin master --tags

# Publish package to PyPI
publish:
    @echo "📦 Publishing to PyPI..."
    @UV_PUBLISH_TOKEN="$(tr -d '\n' < ~/.pypi_token)" uv publish
    @echo "✅ Release completed!"

release: clean-build check test
    @just bump minor
    @just build
    @just publish
