# Deploy

Installs a built wheel onto the bot host and restarts the unit. Same playbook
from a laptop and from CI; only the vault password and the host address differ.

## Host prerequisites

An SSH user (`deploy` by default, `DEPLOY_USER` overrides) with **passwordless**
sudo — neither path passes `--ask-become-pass`.

That is all. The host python is irrelevant: gravelines is Debian 12 with Python
3.11, the wheel needs `>=3.13`, so the playbook has `uv` fetch the interpreter.
It installs `uv` only if the host has none, since other services may share it.

The playbook creates the `krcg-bot` system user, `/opt/krcg-bot/venv`, the cache
directory, the token file and the systemd unit. It never puts the token in the
unit: an inline `Environment=` is readable by anyone who can run `systemctl cat`.

## The vault

`vault.yml` holds one variable, `discord_token`, and is committed **encrypted**.
Create it once:

```bash
cd ansible
ansible-vault create vault.yml     # discord_token: <the bot token>
```

Then add the same password as the `ANSIBLE_VAULT_PASSWORD` GitHub secret, so CI
and the laptop run one code path.

> This repo is public, so the vault publishes the ciphertext of a live bot
> token. Lionel accepted that (T-001). `ansible-vault` uses PBKDF2 at 10 000
> iterations, which is weak against an offline attack, so the passphrase has to
> be long and random. A pre-commit hook refuses an unencrypted `vault.yml`.
> The escape hatch, if that ever stops being acceptable: `-e discord_token=...`
> overrides `vault.yml`, since extra-vars outrank `vars_files`.

CI also needs `ANSIBLE_VAULT_PASSWORD` on the `production` environment. Today
that environment holds only the `DEPLOY_SSH_KEY` secret, plus the `DEPLOY_HOST`
and `DEPLOY_HOST_KEY` *variables*.

## Deploying

From the laptop — builds the wheel, then converges:

```bash
DEPLOY_HOST=<host> just deploy
```

It prompts for the vault password unless `ANSIBLE_VAULT_PASSWORD_FILE` is set.

From CI: `.github/workflows/deploy.yml` runs on a published GitHub release
(`just github-release`, or the GitHub UI) and on `workflow_dispatch`. It reads
`DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_HOST_KEY` and `ANSIBLE_VAULT_PASSWORD`
from the `production` environment.

## What a converge does

Nothing, if nothing changed: the wheel is only installed when the artifact
differs, and only that install, the token file and the unit notify a restart. A
restart drops the buttons on live messages and re-fetches the corpus, so a
no-op converge deliberately leaves the gateway alone.

It ends by waiting for the unit to come up, then checking 20s later that it is
still the same run — `Restart=always` means a crash-looping bot passes through
`active` between restarts, and a deploy that leaves the bot down is a failed
deploy.

## First converge

The bot already runs on gravelines from a hand-made `krcg-bot.service` at the
same path this playbook writes, as `User=lpanhaleux` out of
`/home/lpanhaleux/projects/krcg-bot`. Checked, and it decides the cutover:
taking over the same unit name means systemd stops the old process before
starting the new one, so there is no window with two gateways on one token. On
any other host, check first — a differently-named unit left enabled *is* that
window:

```bash
systemctl list-unit-files --type=service | grep -i krcg
```

Two consequences of that cutover:

- **The vault must hold the token the bot runs on today.** It lives inline in
  the current unit, which this playbook overwrites; read it out first. The
  overwrite is backed up on the host, but a wrong token means a crash loop.
- The old tree under `/home/lpanhaleux/projects/krcg-bot` is left alone, and is
  yours to remove once the new unit is up.

`just deploy` is outside the workflow's `concurrency` group: converging from the
laptop while CI converges restarts the bot twice.
