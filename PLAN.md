# PLAN

next-ticket-id: T-006 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

Line format: `T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN`

## Now

T-005 — Correct the stale README badges — todo — tickets/T-005.md

## Next

(empty)

## Backlog

(empty)

## Queue (topics not yet filed — run /ticket)

Sanctioned pre-ticket pen — reminders awaiting `/ticket` grilling with Lionel, not tickets:

- `_build_components` can emit more than Discord's 5 action rows: `len(ret) >= 5` breaks only the inner loop, then a trailing append runs unconditionally. Button labels are not capped at the 80-char limit either. Found by `eng` while advising T-003
- Switch from a gateway bot to a hook-based (HTTP interactions) bot. Lionel: "there are good tunneling solutions I think discord itself documents to achieve this". Testability was the sole reason for the gateway, so a tunnel removes that objection — verify what Discord actually documents (context7/current docs, not recall) before filing. Strategic: changes the runtime shape, the hosting story, and what `ansible/` deploys
- README states Python 3.8 and the black code style; the project is Python 3.13 + ruff
