---
name: ticket
description: File a work item into the plan. The ONLY way work lands in PLAN.md/tickets/ — use whenever Lionel, an agent, or user feedback proposes work, a decision, or a roadmap item.
argument-hint: [request]
---

# /ticket

Runs inline in the main conversation only — grilling needs AskUserQuestion, which subagents lack. A subagent with a proposal returns it; the main loop files on its behalf.

## Procedure

1. **Intake.** Capture the request verbatim and the requestor: `lionel` | agent name | `user-feedback`.

2. **Context.** Read `PLAN.md` and `refs/shared/plan-format.md`. Surface duplicates or conflicts to the requestor instead of filing.

3. **Route by what the ticket changes, not its blast radius.** product/scope → `pm`; technical → `eng`; harness/process → `harness`; several only when the ticket itself changes several domains. Spawn only those advisors, in parallel, via the Agent tool, passing the request verbatim.

4. **Grill the requestor.**
   - `lionel` → AskUserQuestion with the advisors' hardest questions. ≤4 per round, ~3 rounds; stop as soon as answers stop changing the ticket.
   - agent → SendMessage the proposer with those questions; if not resumable, spawn its type fresh with the proposal + questions. Record the answers.
   - `user-feedback` → no grilling; unanswered questions become Open questions.
   - Settle the section (Now/Next/Backlog) during grilling; routine defaults to Backlog.

5. **Synthesize.** Draft per plan-format. Classify tier per `CLAUDE.md`.

6. **Land it.** Allocate `T-NNN` per plan-format, write `tickets/T-NNN.md` (no status or priority fields), add the PLAN.md line under the chosen section with status `todo` — `awaiting-sign-off` plus a summary to Lionel when strategic, or `todo`/`in-progress` when he signed off live during grilling, recorded in the ticket — and bump the counter. Commit `T-NNN: filed — <one-line why>`; several tickets from one request share one commit.

   A filing commit touches `tickets/` and `PLAN.md`, nothing else. A constraint grilling settled is recorded in the ticket and lands in the doc it governs when the ticket ships or is dropped (plan-format §Lifecycle).

## Token discipline

No advisor outside its domain. Advisor replies ≤150 words. Do not pad grilling rounds. Ticket body budget: plan-format §Ticket file.
