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

## Vault password

The vault password itself lives **in the repo, age-encrypted**, decryptable only
by the keys in `secrets/age-recipients.txt`. Install
[`age`](https://github.com/FiloSottile/age) first. `ansible.cfg` points
`vault_password_file` at the git-ignored `.vault_pass`, so decrypt into that and
every command below just works:

```bash
cd ansible
age -d -i ~/.ssh/<your-key> -o .vault_pass secrets/vault-pass.age
```

CI writes the same file from the `ANSIBLE_VAULT_PASSWORD` secret, so both paths
run one command with no `--vault-password-file` anywhere.

### Adding a recipient

Recipients are the public keys in `secrets/age-recipients.txt` — one per line,
either `ssh-ed25519`/`ssh-rsa` (e.g. a line from `https://github.com/<user>.keys`)
or `age1…` from `age-keygen`. Editing the list does not re-key anything; an
existing recipient must re-encrypt:

```bash
age -d -i ~/.ssh/<your-key> -o .vault_pass secrets/vault-pass.age   # 1. decrypt
echo 'ssh-ed25519 AAAA… alice' >> secrets/age-recipients.txt        # 2. add their PUBLIC key
age -R secrets/age-recipients.txt -o secrets/vault-pass.age < .vault_pass   # 3. re-encrypt
```

The password is unchanged — you are only widening who can read it. **Removing** a
recipient is the same flow with their line deleted, but that only stops *future*
decrypts: anyone who already decrypted still holds the password. Revoking for
cause means rotating the vault password itself, re-encrypting `vault.yml` with
it, and updating the GitHub secret.

## The vault

`vault.yml` holds one variable, `discord_token`, and is committed **encrypted**.
With `.vault_pass` in place, create it once:

```bash
cd ansible
ansible-vault create vault.yml     # discord_token: <the bot token>
```

> This repo is public, so the vault publishes the ciphertext of a live bot
> token. Lionel accepted that (T-001). `ansible-vault` uses PBKDF2 at 10 000
> iterations, which is weak against an offline attack, so the passphrase has to
> be long and random. A pre-commit hook refuses an unencrypted `vault.yml`.
> The escape hatch, if that ever stops being acceptable: `-e discord_token=...`
> overrides `vault.yml`, since extra-vars outrank `vars_files`.

### Bootstrapping it, in order

Nothing exists yet. Once, from `ansible/`:

```bash
head -c 32 /dev/urandom | base64 > .vault_pass          # 1. a long random password
age -R secrets/age-recipients.txt -o secrets/vault-pass.age < .vault_pass   # 2. share it
ansible-vault create vault.yml                          # 3. discord_token: <the live token>
gh secret set ANSIBLE_VAULT_PASSWORD --env production < .vault_pass         # 4. give CI the same
```

Commit `secrets/vault-pass.age` and `vault.yml`; `.vault_pass` is git-ignored.
The `production` environment currently holds only the `DEPLOY_SSH_KEY` secret,
plus the `DEPLOY_HOST` and `DEPLOY_HOST_KEY` *variables*.

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

`just deploy` is outside the workflow's `concurrency` group: converging from the
laptop while CI converges restarts the bot twice.
