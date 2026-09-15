# Wiki — the map

Source of truth for *what is* and *what was decided*. Code is the source of truth for *how*.
Plans, findings and reasoning journeys do not live here — they die with their task.

## Product

- [product.md](product.md) — scope and capabilities: `/card`, the answer it draws, autocomplete,
  what the bot deliberately does not do.
- [buttons.md](buttons.md) — the buttons on an answer: the navigation trail they carry, their
  expiry, and what an old button does after a deploy.
- [operations.md](operations.md) — local dev, CI, the release, and the deploy on gravelines.

## Dogmas

- [dogmas.md](dogmas.md) — the paradigms chosen by the human: code, errors, state, testing,
  dependencies, records, commits and releases. Ingress and egress check against this page.

## Domain

- [discord.md](discord.md) — Discord's interaction, component and embed limits, and the hikari
  traps this bot sits on.
- [corpus.md](corpus.md) — the card and rulings corpus from upstream `krcg`: how it loads, the shape
  the bot reads, and the couplings the version ceiling guards.

## The board

[`../BOARD.md`](../BOARD.md) holds what must change. Nothing in this wiki is an ask; nothing on the
board is context.
