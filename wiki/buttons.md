# Buttons — the trail, expiry, and old buttons

The buttons under a `/card` answer, and the standing decisions that shape them. Limits they must
respect are on [discord.md](discord.md#components).

## What an answer offers

- **Make public** — on an ephemeral answer only. Replaces it with the same card posted publicly;
  the public copy keeps its card buttons in a server, none in a DM.
- **Variants** — one button per other version of the card (`Base`, or the variant's suffix), for
  vampires with advanced or group versions.
- **Ruling links** — one per card cited in the rulings, deduplicated, on their own row.
- **`< Back`** — once the reader has navigated: returns to the previous card.

Navigating an ephemeral answer redraws it in place. A button on a **public** answer never edits it:
it answers the clicker with a fresh ephemeral that starts its own trail.

## The trail lives in the button (2026-07-27)

**A button carries everything needed to answer it**: the navigation trail is encoded in its
`custom_id` as fixed-width 6-digit card ids, target last — never in server-side state keyed by
message. So a button survives a restart or a deploy, and nothing has to be rebuilt.

- The trail *is* the UI. `< Back` is the trail minus its last frame. A ruling link **descends**: the
  card on screen becomes a frame. A variant **inherits** the trail rather than extending it — it is
  another version of the card on screen, not a step down from it. `< Back` and the parent's own
  ruling link are both offered: one walks up, the other descends.
- Depth is bounded by the 100-character `custom_id`: `MAX_FRAMES` (15). Past it the **oldest** frames
  drop, so a deep trail shortens from its far end. An answer is drawn **one frame short** of the
  ceiling: at the full depth `< Back` and a ruling link spell the same `custom_id` on a trail that
  ping-pongs between two cards (the corpus holds such pairs), and a duplicate is a 400 on the whole
  message.
- **Fixed width holds only while every corpus id is 6 digits.** A wider id desyncs every frame
  parsed after it, silently ([corpus.md](corpus.md#card-ids)).

## When rows run out (2026-07-26)

Buttons fill rows of 5, at most 5 rows. **Make public and `< Back` are never dropped** — `< Back` is
the reader's only way back up the trail. Variants spill onto further rows. **Ruling links go first**,
since autocomplete reaches every one of them again. Every drop is logged: a button vanishing
silently was the defect.

## Expiry: idleness, not age (2026-07-27)

Buttons are stripped once an answer has gone `COMPONENTS_TIMEOUT` (5 minutes) **unused**; each
navigation pushes that back. Make public's public copy is the exception: its buttons go 5 minutes
after posting.

- **Two clocks, and only idleness strips.** A watcher strips through the interaction token it was
  handed, which dies 15 minutes after it started; it never waits past that. When the token is what
  ends the wait, it **leaves the buttons in place**: the reader is still there, the buttons still
  answer on their own, and the next click re-arms a watcher with a fresh token.
- One watcher per message: the claim is also the check, and it is released on every exit.
- A restart abandons the watchers, not the buttons. A click that finds no watcher re-arms one, so
  stripping heals itself. **Accepted residue** — litter for a reader who has gone, never a break for
  one still present: an ephemeral nobody clicks again, one abandoned past the token, and every public
  answer (a click there answers a new ephemeral, so nothing re-arms it).
- **No shutdown hook** stripping buttons on stop. Rejected: it cannot run on SIGKILL, OOM or a
  reboot, and the daily scheduled restart ([operations.md](operations.md#deploy)) would strip working
  buttons every day.

## Old buttons after a deploy (2026-07-29)

A live button outlives both the **corpus** and the **encoding** it names: a deploy leaves the previous
release's buttons clickable until their tokens die.

- A card gone from the corpus answers "This card is gone from the corpus: use the completion
  again!".
- A trail spelled by another encoding answers "This button is out of date: use the completion
  again!". The dispatch key — the first 6 characters of `custom_id`, `switch` — **never changes**, so
  an old button still reaches its handler; a new encoding bumps the **version character** in
  `switch-1`, checked before width and digits, which alone cannot tell two encodings apart. An
  unknown dispatch key would show "Command error" instead.
