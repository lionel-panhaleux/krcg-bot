# Ticket format

## Ticket file
`tickets/T-NNN.md` — the filing record. Immutable after /ticket lands it, except `parent`/`depends-on` corrections. No status, no priority, no dates: state lives in PLAN.md, history lives in git.

```yaml
id: T-NNN
title: <short imperative>
type: epic|task
tier: routine|strategic
requestor: lionel|<agent-name>|user-feedback
advisors: [pm, eng]   # those actually consulted
parent: T-NNN         # tasks only; epics cannot have parents (2 levels max)
depends-on: [T-NNN]   # optional
```

Body: Problem / Outcome / Advisor input (attributed `pm:` `eng:` `harness:`) / Grilling record (incl. live sign-off when used) / Open questions / Tasks. Omit empty sections.

## State lives in PLAN.md only
One line per ticket under the section that IS its priority — Now / Next / Backlog:
`T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN` for their epic.

Status: `todo | in-progress | blocked | awaiting-sign-off`.
`awaiting-sign-off`: strategic tickets only; exits only via Lionel; not workable while set.
Section at filing: requestor's call during grilling; routine defaults to Backlog.

## Lifecycle
- Created ONLY by `/ticket`. Allocate id from `next-ticket-id`, bump the counter. If `tickets/T-NNN.md` already exists (parallel session), take the next free number ≥ counter and bump past it. Never reuse a number.
- Whoever works a ticket updates its PLAN.md line. Section moves are re-prioritization: routine moves freely; strategic moves only with Lionel.
- Done or dropped → delete the ticket file AND its PLAN.md line.
- Epics: deletable only with no live sub-tickets. When the last sub-ticket is deleted, review the epic — file more sub-tickets or delete it.
- Commit discipline: filing and deletion are each committed immediately by the session that did them, message `T-NNN: filed|shipped|dropped — <one-line why>`. Git is the archive; an uncommitted deletion is data loss.

## Recovery
`git log --follow -- tickets/T-NNN.md` — content, dates, and filed/dropped rationale from commit messages.
