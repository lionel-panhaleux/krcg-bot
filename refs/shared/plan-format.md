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

Body budget — ≤40 lines total (T-014). The ticket is read by whoever works it, not by a historian:
- **Problem** — the defect and the evidence for it. Numbers, paths, commits. Not the story of how it was found; git holds that.
- **Advisor input** — verdict and any binding condition. The reasoning was already spent in the ≤150-word reply.
- **Grilling record** — what was settled, by whom, and what was rejected. Not the route to it.
- **Tasks** — imperative, one line each.

## State lives in PLAN.md only
One line per ticket under the section that IS its priority — Now / Next / Backlog:
`T-NNN — title — status — tickets/T-NNN.md` · sub-tickets append ` ← T-NNN` for their epic.

Status: `todo | in-progress | blocked | awaiting-sign-off`.
`awaiting-sign-off`: strategic tickets only; exits only via Lionel; not workable while set.
Section at filing: requestor's call during grilling; routine defaults to Backlog.

## Lifecycle
- Created ONLY by `/ticket`. Allocate id from `next-ticket-id`, bump the counter. If `tickets/T-NNN.md` already exists (parallel session), take the next free number ≥ counter and bump past it. Never reuse a number.
- Whoever works a ticket updates its PLAN.md line. Section moves are re-prioritization: routine moves freely; strategic moves only with Lionel.
- Done or dropped → delete the ticket file AND its PLAN.md line. A constraint the ticket settled that outlives it — a rejection, a "not until X" trigger — is written into the doc it governs (`refs/<agent>/INDEX.md`, a rule, the code) in that same commit (T-013). Not at filing: the home is a guess until the work is done, and a filing that writes outside the plan pulls a review and an audit into bookkeeping. There is no decisions log; a constraint deleted with its ticket is lost.
- Epics: deletable only with no live sub-tickets. When the last sub-ticket is deleted, review the epic — file more sub-tickets or delete it.
- Commit discipline: filing and deletion are each committed immediately by the session that did them, message `T-NNN: filed|shipped|dropped — <one-line why>`. Git is the archive; an uncommitted deletion is data loss. **The subject line is the message** (T-014) — a body only for what the ticket does not already say, such as a constraint housed elsewhere in the same commit. A body restating the ticket duplicates a doc that is one `git show` away.

## Recovery
`git log --follow -- tickets/T-NNN.md` — content, dates, and filed/dropped rationale from commit messages.
