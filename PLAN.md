# PLAN

next-ticket-id: T-011 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

Line format: `T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN`

## Now

T-010 — Carry the navigation stack in custom_id and delete HISTORY — todo — tickets/T-010.md

## Next

(empty)

## Backlog

(empty)

## Queue (topics not yet filed — run /ticket)

Sanctioned pre-ticket pen — reminders awaiting `/ticket` grilling with Lionel, not tickets:

- Switch from a gateway bot to a hook-based (HTTP interactions) bot. Lionel: "there are good tunneling solutions I think discord itself documents to achieve this". Testability was the sole reason for the gateway, so a tunnel removes that objection — verify what Discord actually documents (context7/current docs, not recall) before filing. Strategic: changes the runtime shape, the hosting story, and what `ansible/` deploys
- `MAX_ACTION_ROWS = 5` and the "≤5 action rows" line in `.claude/rules/bot-code.md` appear on **no current Discord docs page** `eng` could reach (checked 2026-07-26); what is documented is "up to 40 total components" per message and 5 buttons per row. T-008's shipped cap rests on the unsourceable number. Nothing is on fire — 5×5=30 is inside 40 — but re-source both ceilings or state plainly that the row count is folklore
