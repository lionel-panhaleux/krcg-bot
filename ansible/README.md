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

Only a released wheel is ever deployed, from either path — what runs in
production always answers to a tag.

From the laptop, downloading the release artifact and converging it:

```bash
DEPLOY_HOST=<host> just deploy          # the latest release
DEPLOY_HOST=<host> just deploy v4.4     # or roll back to a specific one
```

It prompts for the vault password unless `ANSIBLE_VAULT_PASSWORD_FILE` is set.
There is no path that ships working-tree code: to try a change on the host, cut
a release.

From CI: `.github/workflows/deploy.yml` runs on a published GitHub release
(`just github-release`, or the GitHub UI) and on `workflow_dispatch`. It reads
`DEPLOY_SSH_KEY` and `ANSIBLE_VAULT_PASSWORD` (secrets) plus `DEPLOY_HOST` and
`DEPLOY_HOST_KEY` (variables) from the `production` environment.

**The release carries the wheel it deploys.** `just github-release` attaches it;
both the workflow and `just deploy` download that asset rather than building
one. A release with no wheel attached fails rather than deploying something
else. Redeploying an older release is `workflow_dispatch` with its tag, or
`just deploy <tag>`.

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

Nothing is deployable yet: the repo has **no GitHub releases**, so there is no
wheel to download. `just release` cuts the first one — which also pushes master
and, until T-004 lands, publishes to PyPI. Cutting it by hand instead is
`just build` then `gh release create vX.Y --generate-notes dist/*.whl`.


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
