# Project

Durable facts.

## What it is
A Discord bot that displays V:tES cards: official text, image, and KRCG rulings. One slash command, `/card <name>`, with name autocompletion and an optional `public` flag; answers are ephemeral by default. Buttons on the answer: make public, switch between card variants (base/advanced/evolution), jump to cards cited in rulings, and come back.

## Users
V:tES players, mid-game or mid-discussion, on any Discord server. The bot must answer instantly and need no learning: autocomplete is the whole interface. No account, no config, no per-server setup beyond installing it — with one optional nicety: if the server defines discipline/icon emojis by their VEKN names, card text renders with them.

## Data
Card texts come from the VEKN official card lists, rulings from the KRCG rulings list, both via the `krcg` python package (upstream: `lionel-panhaleux/krcg`). Data is loaded from the KRCG static server at startup and held in memory — the bot ships no card data of its own, and a restart is how it picks up new cards or rulings.

## Distribution
One instance, hosted by Lionel, installable on any Discord server via the OAuth link in the README. Self-hosting is not supported and is no longer documented (Lionel, T-004). The PyPI package served mirrors rather than people and is archived — not yanked, not deleted — leaving it installable, unmaintained, with the name held.

## Governance
MIT. Issues, discussions and contribution guidelines live in the upstream `krcg` repository, not here — this repo is the bot only. Card materials are Paradox Interactive copyrights and trademarks, used with permission (Dark Pack); the attribution in the README and the footer icon in card embeds are not optional.

## Team
Lionel: solo, side-project pace. Plus AI agent fleet — the harness optimizes autonomous agent throughput between check-ins.
