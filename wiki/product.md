# Product

**krcg-bot** — a Discord bot that shows a V:tES card: its official text, image and KRCG rulings.
Players reach for it mid-game or mid-argument, on any server, so it must answer at once and need no
learning: autocomplete is the whole interface. One instance, hosted by Lionel, installable on any
server through the OAuth link in the README.

Card texts come from the VEKN official card lists, rulings from the KRCG rulings list, both through
the `krcg` package ([corpus.md](corpus.md)). The bot ships no card data of its own.

## Capabilities

**`/card name [public]`** — the one global slash command. `name` (at least 3 characters) is
autocompleted; `public` defaults to false. The answer is **ephemeral unless `public`** is set. A name
that is not a card is refused ephemerally: "Unknown card: use the completion!".

**Autocomplete.** Up to **25** card full names matching the typed text. Every card in the corpus is
offered when its full name is typed. An empty name, or a corpus not yet loaded, answers no choices
rather than an error.

**The answer.** One embed, titled with the card's unique name (which tells same-named variants
apart) and linking to the card on codex-of-the-damned.org, where rulings are submitted. Its colour
follows the card type, or the clan for a crypt card. It carries:

- the card image, its URL cache-busted by the hour;
- **Type** — the types, and "(Burn Option)" when the card has one;
- crypt cards: **Clan** with capacity and group, and **Disciplines**;
- library cards: **Clan** for a clan requirement, and **Cost**;
- **Card Text** — card names and `/phrases/` in italics;
- **Rulings** — "BANNED since …" first when banned, then one bullet per ruling, cited cards in
  italics and references as links. Rulings too long for one field move to further embeds titled
  "… — Rulings";
- the Dark Pack attribution: footer icon and text, on every answer. Not optional
  ([dogmas.md](dogmas.md#records)).

**Guild emojis.** The one optional nicety: when a server defines emojis named for disciplines or
card icons, disciplines and the `[tokens]` in card text render with them. Nothing else is
configurable, and nothing is required to get a correct answer.

**Buttons.** Make public, card variants, cards cited in rulings, and `< Back` —
[buttons.md](buttons.md).

**Failures.** A refusal the reader can act on is answered ephemerally with its reason. Too many
commands at once answers "Error: too many commands, wait a bit and try again."; anything else
"Command error", logged.

## Deliberately not

- **Nothing posts publicly without an explicit act** — `public`, or Make public. Ephemeral by default
  is the feature: the bot must not spam a channel.
- **No per-server configuration.**
- **Display and navigation only.** Deck building, tournament tooling and rulings authoring live in
  the sibling projects (`krcg`, archon, the rulings list).
- **No self-hosting, no PyPI package** — one hosted instance ([dogmas.md](dogmas.md#releases-and-deploys)).
- **No database**, and no state a restart cannot rebuild ([dogmas.md](dogmas.md#state)).

## Governance

MIT. Issues, discussions and contribution guidelines live in upstream `krcg`, not here — this repo
is the bot only. Card materials are Paradox Interactive copyrights and trademarks, used with
permission (Dark Pack).

## Status (2026-09-15)

**4.10** runs on gravelines, deployed by this repo's `deploy.yml` from its GitHub release
([operations.md](operations.md#deploy)).
