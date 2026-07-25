# refs/eng

Scope: architecture, Discord/hikari integration, upstream `krcg` coupling, packaging, release, hosting, quality gates.

## Stack
- Python ≥3.13, `uv` + `uv_build` backend, src layout. Deps: `hikari`, `krcg>=4.16`, `unidecode`. Dev: `ipython`, `mypy`, `pytest`, `ruff`.
- The bot is one module: `src/krcg_bot/__init__.py` plus a three-line `__main__.py`. Keep it that way until a second surface justifies splitting.
- `hikari.GatewayBot` — a gateway (websocket) bot, not an HTTP interactions endpoint. Single process, in-memory state, no database. The gateway is chosen for testability, not inertia: an interactions endpoint needs a public HTTPS URL Discord can reach, while the gateway dials out — so the dev token runs the real bot from a laptop against a test guild. Testability is the argument, and a tunnel may answer it — unverified. Switching to a hook-based bot is an open topic (PLAN.md Queue), not a settled prohibition.
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
- Tests run against the **live corpus**, always. A committed card fixture was proposed and rejected (Lionel, T-003): tests assert against the data the bot actually serves. Consequence to accept, not fix: the suite needs the network, and a KRCG static-server outage reds unrelated PRs.
- Manual verification of Discord-facing changes — krcg dev token, `.env`, test guild: `.claude/rules/bot-code.md` §Verification, which is its home and loads when the code is touched.
- CI: `.github/workflows/test.yml` on PRs and pushes to master — uv, py3.13, `just quality` + `just test`. Broken as of T-003: `origin/master` still has the old `static.yml`, red since 2025-08.
- Release (Lionel only): `just release` = clean, master + clean-tree check, test, `uv version --bump minor`, commit `Release X.Y`, tag, push, build, publish to PyPI. `CHANGELOG.md` is hand-written, newest first.
- **No release while the suite is a stub or CI is red** (Lionel, T-003). Gate, not preference.
- Hosting: PyPI install in a venv, `DISCORD_TOKEN` in the environment, systemd unit with `Restart=always` (README has the unit).
- Deploy automation lives in this repo, not in server-setup (Lionel, T-001): server-setup ships only `nginx_site` and `postgres_db`, and a gateway bot has no listener and no database. That rejection is the standing part; the mechanics are T-001's.

## Shared
- `refs/shared/project.md` — what the bot is, users, data sources, governance.

## Grilling angles
- Which Discord API limit does this hit first — rows, field length, the 3s acknowledge budget?
- What does it cost at startup and in memory, given the whole corpus is resident?
- Does it survive a restart, and what happens to live components and `HISTORY` if not?
- What does it assume about upstream `krcg` (data shape, rulings format, version floor) — and how does it fail when that changes?
- How is it verified? The suite is a stub: name the manual check, or the test that stops being a stub.
- Does it still work with zero server configuration (no custom emojis, no permissions beyond the default)?
