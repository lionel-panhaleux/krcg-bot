# refs/eng

Scope: architecture, Discord/hikari integration, upstream `krcg` coupling, packaging, release, hosting, quality gates.

## Stack
- Python ≥3.13, `uv` + `uv_build` backend, src layout. Deps: `hikari`, `krcg>=4.16`, `unidecode`. Dev: `ipython`, `mypy`, `pytest`, `ruff`.
- The bot is one module: `src/krcg_bot/__init__.py` plus a three-line `__main__.py`. Keep it that way until a second surface justifies splitting.
- `hikari.GatewayBot` — a gateway (websocket) bot, not an HTTP interactions endpoint. Single process, in-memory state, no database.
- Tooling: ruff (line-length 100, target py313), mypy on `src/krcg_bot` with untyped defs disallowed, pre-commit (ruff + whitespace/yaml hooks).

## Runtime shape
- Startup: `vtes.VTES.load()` pulls the full card + rulings corpus from the KRCG static server into memory, then the gateway connects. No card data ships in the package; a restart is the only refresh path.
- Commands are registered in `on_ready` by diffing names against the application's registered commands, then dispatched through `COMMANDS` (by command id) and `COMPONENTS` (by the 6-char `custom_id` prefix: `public`, `switch`). Adding a surface means touching those tables.
- Guild emojis are cached per guild in `EMOJIS` on `GuildAvailableEvent`; discipline/icon names come from `vtes.VTES.search_dimensions["discipline"]` plus `EMOJI_NAME_MAP`.
- `HISTORY` maps a message id to its card-navigation stack, in memory, ephemeral messages only.
- Every card response holds its handler coroutine in `asyncio.sleep(COMPONENTS_TIMEOUT)` (300s) before stripping components — a live task per answer, and a restart abandons them (buttons stay on old messages and fail).
- Error paths all funnel through `CommandFailed` (expected, message shown) vs. anything else (logged, "Command error"), with a webhook follow-up fallback when the interaction is already acknowledged.

## Discord limits that shape the code
Embed field value ≤1024 (rulings overflow into extra embeds), embed description ≤4096 (`_split_text`), ≤5 action rows per message, ≤5 buttons per row, ≤25 autocomplete choices, 3s to acknowledge an interaction (`_autocomplete_cache` exists for that reason).

## Workflow
- `just quality` — ruff format check, ruff check, mypy. `just test` — quality then pytest. `just serve` — run locally from `.env`.
- Tests: `tests/conftest.py` fails the session without internet and without the KRCG static server, then loads the corpus; `tests/test_bot.py` is a stub. Treat the suite as a smoke test, not a safety net — verify Discord-facing changes by running the bot.
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
