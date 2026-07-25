# PLAN

next-ticket-id: T-004 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

Line format: `T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN`

## Now

T-001 — Move deploy to an in-repo Ansible pipeline — todo — tickets/T-001.md
T-002 — Port to krcg 5 — awaiting-sign-off — tickets/T-002.md
T-003 — Replace the stub suite and repair CI — awaiting-sign-off — tickets/T-003.md

## Next

(empty)

## Backlog

(empty)

## Queue (topics not yet filed — run /ticket)

Sanctioned pre-ticket pen — reminders awaiting `/ticket` grilling with Lionel, not tickets:

- Stop publishing to PyPI. Lionel, while grilling T-002: "we'll stop using pypi anyway". Strategic — changes the Distribution fact in `refs/shared/project.md`, the README self-hosting instructions (`pip install krcg-bot`), and `just release`, which currently tags/pushes/builds/publishes as one recipe. T-001's release-triggered deploy needs that recipe split
- `_build_components` can emit more than Discord's 5 action rows: `len(ret) >= 5` breaks only the inner loop, then a trailing append runs unconditionally. Button labels are not capped at the 80-char limit either. Found by `eng` while advising T-003
- Switch from a gateway bot to a hook-based (HTTP interactions) bot. Lionel: "there are good tunneling solutions I think discord itself documents to achieve this". Testability was the sole reason for the gateway, so a tunnel removes that objection — verify what Discord actually documents (context7/current docs, not recall) before filing. Strategic: changes the runtime shape, the hosting story, and T-001's deploy target
- README states Python 3.8 and the black code style; the project is Python 3.13 + ruff
