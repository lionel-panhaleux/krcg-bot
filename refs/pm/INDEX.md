# refs/pm

Scope: product scope, user value, prioritization, roadmap coherence, ticket quality.

## Product line
- The bot answers one question — "what does this card say, and how does it rule?" — during a game or an argument. Speed and zero learning curve beat capability.
- Scope guard: display and navigation. Deck building, tournament tooling and rulings authoring live in the sibling projects (`krcg`, `archon`, the rulings list), not here.
- Ephemeral by default is a feature: the bot must not spam a channel. Anything that posts publicly without an explicit user act is a regression.
- No per-server configuration. Optional niceties (guild emojis) may improve output; nothing may be required to get a correct answer.

## Shared
- `refs/shared/project.md` — users, data sources, distribution, governance.
- `refs/shared/decisions.md` — decisions in force.
- `refs/shared/plan-format.md` — ticket spec.

## Grilling angles
- Which player, in which moment — mid-game, mid-argument, deck-building at home?
- Does it survive the interface budget: one command, autocomplete, one answer? What does it add to the answer that a player will read?
- What breaks if we never build it — and who complains, where?
- Smallest shippable slice: what is the 20% that proves the 80%?
- Is this the bot's job, or the upstream `krcg` project's?
- Maintenance cost: this is a side project running unattended. Who pays when it breaks at 2am?
