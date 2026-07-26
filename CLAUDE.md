# krcg-bot

Discord bot displaying V:tES cards, texts and rulings, from the VEKN official card lists and the KRCG rulings list. Durable facts: `refs/shared/project.md`.

## Standing rules

1. Never use plan mode. `PLAN.md` + `tickets/` are the plan of record.
2. Work items enter the plan ONLY via the `/ticket` skill. No exceptions.
3. Current-state only: delete done/dropped tickets and stale docs. Git is the history.
4. Docs are AI-first — agents are the readers and reviewers. Terse, structured, one fact one home; `refs/` is that home.
5. Main session: read `PLAN.md` at session start and surface any `awaiting-sign-off` tickets to Lionel first. Subagents: skip `PLAN.md` unless the task concerns the plan. Before product or technical work read the matching `refs/<agent>/INDEX.md`.
6. Commit autonomously with plain messages; plan changes use `T-NNN: filed|shipped|dropped — <why>` tombstones. Never push, tag, release or publish without Lionel.
7. Session end is hook-gated: if `CLAUDE.md`, `refs/`, or `.claude/` changed since the last `harness-audit:` commit, run the scoped audit (`refs/harness/INDEX.md`) and commit with the marker (`--allow-empty` if clean).

## Working doctrine

- Finish forward: improvements discovered on task are part of the task; finishing sweeps every consequence. Finish = complete and consistent, not maximal: speculative polish against unstable facts stays unbuilt. De-scope to `/ticket` only on a genuine track-change — adding capability or surface (observable: new files, commands, interfaces).
- Defer only on a named trigger: missing external fact, pending sign-off (existing as a PLAN.md ticket), or observed evidence — "needs Lionel" alone is not a trigger. Never for effort. No TODO notes in docs or code — a deferral is a ticket, a PLAN.md Queue entry awaiting grilling, or it dies.
- Verify before done: `just quality` passes, plus the check `refs/eng/INDEX.md` §Workflow names for the surface you touched. Show the evidence — the command and what it returned — never an assertion that it works.
- Substantive changes get an independent agent review before commit.
- Style: KISS, local, DRY, short. No narration comments, no explanation-in-code, no patterns added for human readability.
- Tech claims: current docs first (context7), never training-data recall — for any stack, version, or API question.
- Game-domain claims: the `vtes` skill is the reference for cards, rules and rulings. Never answer from recall.

## Approval tiers

- **Routine**: lands when `/ticket` grilling completes.
- **Strategic** (new user-facing command or surface, dependency/runtime-floor changes, hosting or release-process changes, anything published to PyPI or pushed to the public repo (Lionel, T-003: this holds even when the push is incidental to the ticket's point, such as pushing a workflow to see CI run), meaning-changes to constitutional docs — project facts, Working doctrine, plan format): status `awaiting-sign-off` until Lionel approves. Meaning-preserving edits to constitutional docs are routine; their independent review must confirm zero meaning drift.

## Map

| Path | Purpose |
|---|---|
| `PLAN.md` | Plan index |
| `tickets/` | One file per active ticket |
| `refs/shared/` | Project facts, plan format |
| `refs/{pm,eng,harness}/` | Per-agent knowledge, pull-based |
| `src/krcg_bot/` | The bot — one module |
| `tests/` | The gate: shape and Discord limits over the live corpus |
| `ansible/` | Deploy of the one hosted instance, and its vault |
| `.claude/agents/` | Agents: pm, eng, harness |
| `.claude/rules/` | Constraints that load themselves when matching files are touched |
| `.claude/hooks/` | Plan brief at session start, harness audit at session end |
| `.claude/skills/ticket/` | `/ticket` — the only gate into the plan |
