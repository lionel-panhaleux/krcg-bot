# refs/eng/deploy

Scope: cutting a release, and how the one hosted instance gets it. Read before `just release`, before touching `ansible/`, and before changing anything about how the bot runs on the host.

## Release

- Release (Lionel only): `just release` = clean, master + clean-tree check, test, `uv version --bump minor`, commit `Release X.Y`, tag, push, then `gh release create` with the wheel — that last step is what fires the deploy. `CHANGELOG.md` is hand-written, newest first. No PyPI publish (T-004); `just release` still pushes master, which is inherent — a GitHub release needs the tag pushed.
- **No release until CI is green on the remote** (Lionel, T-003). Gate, not preference, and it stands for every release. Both halves are met as of v4.6: the suite is real, and `test.yml` is green on `origin/master`.
- `gh release create` **with the wheel attached** is what fires `deploy.yml`. A tag push alone creates no release and so does not deploy.
- One artifact per release, and **nothing else is deployable** (Lionel, T-001): the release carries the wheel, and both CI and `just deploy` converge *that file*. No path ships a working-tree build, so what runs in production always answers to a tag, and rollback is `just deploy <tag>` or `workflow_dispatch` with it. Builds are byte-reproducible (`uv build` twice over one source gives one sha256), so rebuilding would have been *correct* — it was rejected anyway: two artifacts claiming to be one release, and no way to redeploy an old one. Consequence to accept: trying a change on the host means cutting a release.

## Distribution

- The `krcg-bot` PyPI project **is archived** (Lionel, T-004; `project-status: archived` on the simple API, installs still resolve). **Never yank or delete it.** A freed name is a credential-harvest squat: the package takes a `DISCORD_TOKEN`, and whoever would install a squatted `krcg-bot` is exactly the self-hoster this project stopped serving. Holding the name is the standing part, whatever else changes.
- Hosting: one instance, Lionel's, deployed by `ansible/`. Self-hosting was dropped (T-004) — no PyPI package to install, no documented venv/systemd path, and the README no longer carries one. A change to how the bot runs has exactly one consumer now.

## Deploy

- Deploy automation lives in this repo, not in server-setup (Lionel, T-001): server-setup ships only `nginx_site` and `postgres_db`, and a gateway bot has no listener and no database. `ansible/` ships the wheel to the host — no PyPI at deploy time, no git on the host — and `ansible/README.md` is its home: prerequisites, the vault, both trigger paths.
- The host python is not used: gravelines is Debian 12 with Python 3.11 and the wheel needs ≥3.13, so the playbook has `uv` fetch the interpreter (Lionel, T-001: "deploys simply deploy uv and use it to get the python they want"). It installs `uv` only when absent — other services on the host share it.
- The corpus cache is a UID trap. `krcg` writes `krcg_cards_<version>.pkl` into `TMPDIR`, and `load_online` *swallows* the `PermissionError` when that file belongs to another user — then falls back to reading it. Changing the runtime user without redirecting `TMPDIR` therefore pins the bot to a stale corpus forever, silently, with the unit `active`. The unit sets `TMPDIR` to a service-owned directory.
- The corpus refresh is a **scheduled restart**: the unit carries `RuntimeMaxSec=1d`, so systemd stops the bot daily and `Restart=always` brings it back on fresh data. Inherited from the legacy `myserver` deploy (`pw_daily_restart`), retired once `ansible/` converged, which also set `PYTHONOPTIMIZE=1` — kept, so `__debug__` is off and logging stays at INFO instead of DEBUG-logging every query to the journal. Dropping either is a silent regression: stale cards, or a noisy journal.
- A converge restarts only when the artifact, the token or the unit changed — a restart drops the buttons on live messages and re-fetches the corpus. Installs force `--reinstall`: uv and pip both skip a same-version wheel and still exit 0, which would report a successful deploy of code that never landed. It then checks the unit is the *same run* 20s later, since `Restart=always` makes a crash-looping bot look `active`.

## Secrets

- Two secrets are shared through the repo, **age-encrypted** to the public keys in `ansible/secrets/age-recipients.txt` (Lionel — the pattern is copied from `rulings-website`): the ansible-vault password, and `dev-env.age`, the development `.env` that `just serve` needs. One recipients list serves both, deliberately — two lists would drift, and the directory is `ansible/secrets/` only because that list already lived there. `ansible.cfg` points `vault_password_file` at the git-ignored `ansible/.vault_pass`; a developer age-decrypts into it, CI writes the same file from the `ANSIBLE_VAULT_PASSWORD` secret, and no path passes `--vault-password-file`. That file must exist before `--syntax-check`, not just before the converge — ansible resolves vault secrets at parse time. Removing a recipient only stops future decrypts; revoking for cause means rotating the vault password itself.
- CI credentials are split by kind, and mixing them up fails silently: `DEPLOY_SSH_KEY` and `ANSIBLE_VAULT_PASSWORD` are **secrets**, `DEPLOY_HOST` and `DEPLOY_HOST_KEY` are **variables** (`vars.`, not `secrets.` — and not masked in logs). server-setup's `just sync`/`sync-key` is what sets them.
