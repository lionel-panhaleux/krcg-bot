---
paths:
  - "src/krcg_bot/**"
  - "tests/**"
---

# Bot code invariants

Discord API limits. Breaking one fails at runtime, not in review:

- Embed field value ≤1024 chars; embed description ≤4096 (`_split_text` exists for this).
- ≤5 action rows per message, ≤5 buttons per row, ≤25 autocomplete choices.
- An interaction must be acknowledged within 3s (`_autocomplete_cache` exists for this).

Shape:

- One module, no database, no state a restart cannot rebuild.
- Dispatch is table-driven: a new command means an entry in `COMMANDS_TO_REGISTER`, a new component an entry in `COMPONENTS`, keyed by the first 6 chars of `custom_id`.
- Every card answer holds its handler in `_expire_components` before stripping them. That is `COMPONENTS_TIMEOUT` **and then some**: each navigation pushes `EXPIRY` back, so the wait measures idleness, not age. Bounded by the interaction token's 15-minute life — never wait past it, or the strip fails while the buttons still answer. Anything you add after that call runs minutes later, in a task a restart kills.
- Expected failures raise `CommandFailed(msg)` — the user sees `msg`. Everything else is logged and shows "Command error".
- Card and rulings data comes from `krcg`. Never hardcode card facts.
- An autocomplete interaction has no `create_initial_response`, so the error funnel cannot answer it: a raise there hangs the completion. Never let one escape.

Verification: `just quality` must pass. `just test` needs internet and the KRCG static server: it asserts shape and limits over the live corpus, and picks its cards by shape, never by name — assert what a card *is*, never its text. It reaches no Discord interface; the only stand-in is `FakeInteraction`, for autocomplete, pinned to hikari's signature by a test. A Discord-facing change is still only verified by running the bot: `just serve` with the krcg dev token in `.env`, against a test guild.
