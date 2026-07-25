---
name: ticket
description: File a work item into the plan. The ONLY way work lands in PLAN.md/tickets/ — use whenever Lionel, an agent, or user feedback proposes work, a decision, or a roadmap item.
argument-hint: [request]
---

# /ticket

Runs inline in the main conversation ONLY — grilling needs AskUserQuestion, which subagents never have. A subagent with a work proposal returns it in its report; the main loop runs /ticket on its behalf.

## Procedure

1. **Intake.** Capture the request verbatim and the requestor type: `lionel` | agent name | `user-feedback`.

2. **Context.** Read `PLAN.md` and `refs/shared/plan-format.md`. Check for duplicate or conflicting tickets — if found, surface them to the requestor instead of filing.

3. **Route by subject.** Route by what the ticket changes, not its blast radius — a process/doctrine ticket is harness-only even if it affects all future work. product/scope → `pm`; technical → `eng`; harness/process → `harness` (its output contract travels in the spawn prompt); several only when the ticket itself changes several domains. Spawn ONLY the relevant advisors, in parallel, via the Agent tool. Pass the request verbatim. Each returns position / top risks / hardest questions per its output contract.

4. **Grill the requestor.**
   - `lionel` → AskUserQuestion with the advisors' hardest questions. ≤4 per round, up to ~3 rounds; stop as soon as answers stop changing the ticket.
   - agent → SendMessage the proposing agent (resumable with context intact) with the advisors' questions; if not resumable, spawn its agent type fresh with the proposal + questions. Record the answers either way.
   - `user-feedback` → skip grilling; carry unanswered questions into Open questions.
   - Always settle the target section (Now/Next/Backlog) during grilling; routine defaults to Backlog.

5. **Synthesize.** Draft the ticket per plan-format. Classify tier — strategic criteria are in `CLAUDE.md`.

6. **Land it.** Allocate `T-NNN` per plan-format (collision rule applies), write `tickets/T-NNN.md` (filing record — no status/priority fields), add the PLAN.md line under the chosen section with status `todo` (strategic: `awaiting-sign-off` and a summary to Lionel — or `todo`/`in-progress` directly when Lionel signed off live during grilling, recorded in the ticket), bump the counter. Commit: `T-NNN: filed — <one-line why>`.

7. **Decisions.** If a durable decision was made, append one line to `refs/shared/decisions.md`.

## Token discipline

No advisor spawned outside its domain. Advisor replies ≤150 words. Do not pad grilling rounds.
