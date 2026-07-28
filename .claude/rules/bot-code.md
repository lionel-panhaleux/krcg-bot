---
paths:
  - "src/krcg_bot/**"
  - "tests/**"
---

# Bot code invariants

Discord API limits. Breaking one fails at runtime, not in review:

- Embed field value ≤1024 chars; embed description ≤4096 (`_split_text` exists for this).
- ≤5 action rows per message, ≤5 buttons per row, ≤25 autocomplete choices. The row cap is the *legacy* message limit; the wider 40-component ceiling requires the `IS_COMPONENTS_V2` flag, under which `content` and `embeds` stop working — so reaching for 40 means giving up the embed every card answer is built on. Sourced 2026-07-28, `docs.discord.com/developers/components/reference` (read the raw page: fetch summarizers drop these lines).
- `custom_id` ≤100 chars, and the trail encoding spends them: 97 at full depth. Not headroom.
- An interaction must be acknowledged within 3s (`_autocomplete_cache` exists for this).

Shape:

- One module, no database, no state a restart cannot rebuild.
- Dispatch is table-driven: a new command means an entry in `COMMANDS_TO_REGISTER`, a new component an entry in `COMPONENTS`, keyed by the first 6 chars of `custom_id`.
- **A button carries everything needed to answer it.** The navigation trail is encoded in `custom_id` as fixed-width 6-digit card ids, target last (`_switch_id`/`_parse_stack`) — never in a dict keyed by message id. Fixed width holds only while every corpus id is 6 digits; `MAX_FRAMES` derives the depth from the 100-char ceiling and drops the oldest frames past it.
- A live button can outlive **the corpus** it names and **the encoding** that spelled it — a deploy leaves the previous release's buttons clickable until their tokens die. Both are expected failures, not bugs: look cards up through `_card()` and parse through `_parse_stack()`, which raise `CommandFailed`. Changing the `switch-` encoding without changing its 6-char dispatch prefix is what makes old buttons unreadable rather than merely wrong — so the prefix never changes (eng, T-011): an unknown one misses `COMPONENTS` and shows "Command error" instead of a `CommandFailed` the reader can act on.
- `_build_components` renders a stack **one frame short of `MAX_FRAMES`**. At the full ceiling `< Back` and a ruling link truncate to the same frames on a trail that ping-pongs between two cards, and a duplicate `custom_id` is a 400 on the whole message.
- Every `/card` answer holds its handler in `_expire_components` before stripping them — **public ones too**, so `EXPIRY` is not keyed by ephemerals alone; `make_public` is the exception and strips its own message with an inline sleep. That is `COMPONENTS_TIMEOUT` **and then some**: each navigation pushes `EXPIRY` back, so the wait measures idleness, not age. Anything you add after that call runs minutes later, in a task a restart kills.
- Idleness and the token are **two clocks**, and only idleness may strip. A watcher never sleeps past its own token — `TOKEN_LIFETIME` from when *it* started, never from `message.created_at`, or a watcher re-armed on an old message strips on the spot. When the token is what ends the wait, **release without stripping**: the reader is still there, the buttons still answer on their own, and the next click re-arms a watcher that can. Stripping there takes the buttons off a reader mid-argument.
- An `EXPIRY` entry exists **if and only if** a watcher is parked on that message: the claim is also a check — first one in owns the message, the loser returns — and it is released on every exit, by the watcher and by nobody else. A navigation that finds no entry re-arms one, which is the only thing that strips buttons left by a restart. Keep claim and check in the same synchronous run, or two watchers park on one message; and re-check the deadline after stripping, because a click lands mid-PATCH and re-renders the buttons the strip just removed.
- Expected failures raise `CommandFailed(msg)` — the user sees `msg`. Everything else is logged and shows "Command error".
- Card and rulings data comes from `krcg`. Never hardcode card facts.
- An autocomplete interaction has no `create_initial_response`, so the error funnel cannot answer it: a raise there hangs the completion. Never let one escape.

Verification: `just quality` must pass. `just test` needs internet and the KRCG static server: it asserts shape and limits over the live corpus, and picks its cards by shape, never by name — assert what a card *is*, never its text. It reaches no Discord interface; the only stand-in is `FakeInteraction`, for autocomplete, pinned to hikari's signature by a test. A Discord-facing change is still only verified by running the bot: `just serve` with the krcg dev token in `.env`, against a test guild.
