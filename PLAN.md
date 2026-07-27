# PLAN

next-ticket-id: T-011 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

Line format: `T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN`

## Now

(empty)

## Next

(empty)

## Backlog

(empty)

## Queue (topics not yet filed — run /ticket)

Sanctioned pre-ticket pen — reminders awaiting `/ticket` grilling with Lionel, not tickets:

- Switch from a gateway bot to a hook-based (HTTP interactions) bot. Lionel: "there are good tunneling solutions I think discord itself documents to achieve this". Testability was the sole reason for the gateway, so a tunnel removes that objection — verify what Discord actually documents (context7/current docs, not recall) before filing. Strategic: changes the runtime shape, the hosting story, and what `ansible/` deploys
- `MAX_ACTION_ROWS = 5` and the "≤5 action rows" line in `.claude/rules/bot-code.md` appear on **no current Discord docs page** `eng` could reach (checked 2026-07-26); what is documented is "up to 40 total components" per message and 5 buttons per row. T-008's shipped cap rests on the unsourceable number. Nothing is on fire — 5×5=30 is inside 40 — but re-source both ceilings or state plainly that the row count is folklore
- The `custom_id` trail encoding (T-010) has two unguarded fragilities, both raised by `eng` at review and neither urgent. (1) `MAX_FRAMES` holds only while every card id is 6 digits; `test_card_ids_are_fixed_width` reds in CI, but *after* a production bot has already emitted 7-digit frames that `_parse_stack` desyncs into wrong cards, silently. Corpus peaks at 201786, so ~800k ids of headroom. (2) `switch` is shared by both encodings, so `_parse_stack` rejects the previous format by width and digits alone — the next format that happens to be a multiple of 6 digits will parse as plausible ids and answer with the wrong cards. Options are a version character (6 of the 3 spare chars) or bumping the dispatch prefix. Decide whether either is worth building before the trigger, or write both down as accepted
