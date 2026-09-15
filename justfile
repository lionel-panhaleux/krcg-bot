default:
    @just --list

# Install / refresh dev dependencies
update:
    uv sync --upgrade --group dev

# Lint
lint:
    uv run ruff check
    uv run ruff format --check

# Format
fmt:
    uv run ruff check --fix
    uv run ruff format

# Type check
typecheck:
    uv run ty check --error-on-warning

# Run tests (needs the network: they run against the live KRCG corpus)
test:
    uv run pytest -vvs

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
    rm -rf build dist

# Clean build and cache artifacts
clean: clean-build
    rm -rf .pytest_cache .ruff_cache

# Ensure we're on main and the working tree is clean
check:
    @if [[ "$(git branch --show-current)" != "main" ]]; then echo "❌ Not on main"; exit 1; fi
    @if [[ -n "$(git status --porcelain)" ]]; then echo "❌ Working directory is dirty"; exit 1; fi

# Build the package
build:
    uv build

# Bump the version (level: minor | major)
bump level="minor": check
    #!/usr/bin/env bash
    set -euo pipefail
    uv version --bump "{{ level }}"
    # uncoloured: a FORCE_COLOR environment otherwise puts ANSI codes in the tag
    VERSION="$(uv version --short --color never)"
    git add pyproject.toml uv.lock
    git commit -m "Release ${VERSION}" && git tag "v${VERSION}"
    git push origin main --tags

# Publish the GitHub release for the current version, carrying the wheel it deploys
github-release: build
    #!/usr/bin/env bash
    set -euo pipefail
    VERSION="$(uv version --short --color never)"
    WHEEL="$(ls dist/krcg_bot-"${VERSION}"-*.whl)"
    gh release create "v${VERSION}" --generate-notes "${WHEEL}"

release: clean-build check lint typecheck test
    @just bump minor
    @just github-release
