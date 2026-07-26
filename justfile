# Default recipe to list all available recipes
default:
    @just --list

# Lint, format and type check code
quality:
    uv run ruff format --check
    uv run ruff check
    uv run mypy src/krcg_bot

# Run tests & quality
test: quality
    uv run pytest -vvs

# Update dependencies
update:
    uv sync --dev --upgrade

# Serve the bot locally against your test guild (needs .env)
serve:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ ! -f .env ]]; then
        echo "no .env — decrypt the shared dev token:"
        echo "  age -d -i ~/.ssh/<your-key> -o .env ansible/secrets/dev-env.age"
        exit 1
    fi
    set -a && source .env && set +a && uv run krcg-bot

# Deploy a released wheel to the bot host (tag defaults to the latest release)
deploy tag="": clean-build
    #!/usr/bin/env bash
    set -euo pipefail
    : "${DEPLOY_HOST:?set DEPLOY_HOST to the bot host address}"
    # the release is the only source of a deployed artifact: never a local build,
    # or what runs in production answers to no tag
    if [[ -n "{{ tag }}" ]]; then
        gh release download "{{ tag }}" --pattern '*.whl' --dir dist
    else
        gh release download --pattern '*.whl' --dir dist
    fi
    count="$(ls dist/*.whl | wc -l)"
    [[ "${count}" -eq 1 ]] || { echo "expected one wheel on the release, got ${count}"; exit 1; }
    if [[ ! -f ansible/.vault_pass ]]; then
        echo "no ansible/.vault_pass — decrypt it first:"
        echo "  age -d -i ~/.ssh/<your-key> -o ansible/.vault_pass ansible/secrets/vault-pass.age"
        exit 1
    fi
    cd ansible
    uv run --group deploy ansible-playbook deploy.yml -e wheel="$(ls ../dist/*.whl)"

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
    git add pyproject.toml uv.lock
    git commit -m "Release ${VERSION}" && git tag "v${VERSION}"
    echo "📤 Pushing to remote..."
    git push origin master --tags

# Publish the GitHub release for the current version, carrying the wheel it deploys
github-release: build
    #!/usr/bin/env bash
    set -euo pipefail
    VERSION="$(uv version --short)"
    WHEEL="$(ls dist/krcg_bot-"${VERSION}"-*.whl)"
    echo "🚀 Publishing release v${VERSION} with $(basename "${WHEEL}")..."
    gh release create "v${VERSION}" --generate-notes "${WHEEL}"
    echo "✅ Release published — deploy.yml converges that exact wheel"

release: clean-build check test
    @just bump minor
    @just github-release
