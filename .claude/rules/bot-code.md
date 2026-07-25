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
- Every card answer holds its handler in `asyncio.sleep(COMPONENTS_TIMEOUT)` before stripping components. Anything you add after that sleep runs 5 minutes later, in a task a restart kills.
- Expected failures raise `CommandFailed(msg)` — the user sees `msg`. Everything else is logged and shows "Command error".
- Card and rulings data comes from `krcg`. Never hardcode card facts.

Verification: `just quality` must pass. `just test` needs internet and the KRCG static server, and the suite is a stub — a Discord-facing change is only verified by running the bot: `just serve` with the krcg dev token in `.env`, against a test guild. The suite never reaches the Discord interface and is not going to mock it.
