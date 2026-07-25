# PLAN

next-ticket-id: T-001 · Entries land only via `/ticket` (format: `refs/shared/plan-format.md`).

Line format: `T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN`

## Now

(empty)

## Next

(empty)

## Backlog

(empty)

## Queue (topics not yet filed — run /ticket)

Sanctioned pre-ticket pen — reminders awaiting `/ticket` grilling with Lionel, not tickets:

- Test suite is a stub (`tests/test_bot.py` asserts `True`) while `conftest.py` pays a full network + card-load cost
- README states Python 3.8 and the black code style; the project is Python 3.13 + ruff
