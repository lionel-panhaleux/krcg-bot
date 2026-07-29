# PLAN

next-ticket-id: T-017 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

Line format: `T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN`

## Now

(empty)

## Next

(empty)

## Backlog

(empty)

## Queue (topics not yet filed — run /ticket)

Sanctioned pre-ticket pen — reminders awaiting `/ticket` grilling with Lionel, not tickets:

- Switch from a gateway bot to a hook-based (HTTP interactions) bot. Lionel: "there are good tunneling solutions I think discord itself documents to achieve this". Testability was the sole reason for the gateway, so a tunnel may remove that objection — unverified, as `refs/eng/INDEX.md` §Stack also flags it. Verify what Discord actually documents (current docs, whole raw page, not recall) before filing. Strategic: changes the runtime shape, the hosting story, and what `ansible/` deploys
