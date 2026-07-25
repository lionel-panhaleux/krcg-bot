# refs/eng

Scope: architecture, Discord/hikari integration, upstream `krcg` coupling, packaging, release, hosting, quality gates.

## Stack
- Python ≥3.13, `uv` + `uv_build` backend, src layout. Deps: `hikari`, `krcg>=4.16`, `unidecode`. Dev: `ipython`, `mypy`, `pytest`, `ruff`.
- The bot is one module: `src/krcg_bot/__init__.py` plus a three-line `__main__.py`. Keep it that way until a second surface justifies splitting.
- `hikari.GatewayBot` — a gateway (websocket) bot, not an HTTP interactions endpoint. Single process, in-memory state, no database.
- Tooling: ruff (line-length 100, target py313), mypy on `src/krcg_bot` with untyped defs disallowed, pre-commit (ruff + whitespace/yaml hooks).

## Runtime shape
- Startup: `vtes.VTES.load()` pulls the full card + rulings corpus from the KRCG static server into memory, then the gateway connects. No card data ships in the package; a restart is the only refresh path.
- Commands are registered in `on_ready` by diffing names against the application's registered commands. Dispatch is table-driven; a new surface means touching those tables.
- Guild emojis are cached per guild in `EMOJIS` on `GuildAvailableEvent`; discipline/icon names come from `vtes.VTES.search_dimensions["discipline"]` plus `EMOJI_NAME_MAP`.
- `HISTORY` maps a message id to its card-navigation stack, in memory, ephemeral messages only.
- A restart abandons the per-answer component-expiry tasks: buttons stay on old messages and fail.
- Invariants an editor must not break — Discord's hard limits, dispatch tables, the component-expiry task, the error funnel: `.claude/rules/bot-code.md`, which loads automatically when the bot code is touched.

## Workflow
- `just quality` — ruff format check, ruff check, mypy. `just test` — quality then pytest. `just serve` — run locally from `.env`.
- Tests: `tests/conftest.py` fails the session without internet and without the KRCG static server, then loads the corpus; `tests/test_bot.py` is a stub.
- CI: `.github/workflows/test.yml` on PRs and pushes to master — uv, py3.13, `just quality` + `just test`.
- Release (Lionel only): `just release` = clean, master + clean-tree check, test, `uv version --bump minor`, commit `Release X.Y`, tag, push, build, publish to PyPI. `CHANGELOG.md` is hand-written, newest first.
- Hosting: PyPI install in a venv, `DISCORD_TOKEN` in the environment, systemd unit with `Restart=always` (README has the unit).

## Shared
- `refs/shared/project.md` — what the bot is, users, data sources, governance.
- `refs/shared/decisions.md` — decisions in force.

## Grilling angles
- Which Discord API limit does this hit first — rows, field length, the 3s acknowledge budget?
- What does it cost at startup and in memory, given the whole corpus is resident?
- Does it survive a restart, and what happens to live components and `HISTORY` if not?
- What does it assume about upstream `krcg` (data shape, rulings format, version floor) — and how does it fail when that changes?
- How is it verified? The suite is a stub: name the manual check, or the test that stops being a stub.
- Does it still work with zero server configuration (no custom emojis, no permissions beyond the default)?
