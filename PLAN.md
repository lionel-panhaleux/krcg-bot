# PLAN

next-ticket-id: T-009 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

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
- `audit-check.sh` watches only `CLAUDE.md`, `refs/`, `.claude/`. `README.md` carries project facts too — its Python badge said 3.8 for years and no audit trigger ever fired (T-005, unwatched-path leak). Widen the filter, or accept that README facts drift unwatched
