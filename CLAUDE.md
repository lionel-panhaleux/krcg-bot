# krcg-bot

Discord bot displaying V:tES cards, texts and rulings, from the VEKN official card lists and the KRCG rulings list. Durable facts: `refs/shared/project.md`.

## Standing rules

1. Never use plan mode. `PLAN.md` + `tickets/` are the plan of record.
2. Work items enter the plan ONLY via the `/ticket` skill.
3. Current-state only: delete done/dropped tickets and stale docs. Git is the history.
4. Docs are AI-first: terse, structured, one fact one home. `refs/` is that home.
5. Main session: read `PLAN.md` at session start and surface `awaiting-sign-off` tickets to Lionel first. Subagents skip `PLAN.md` unless the task concerns the plan, and read the matching `refs/<agent>/INDEX.md` before product or technical work.
6. Commit autonomously with plain messages; plan changes use `T-NNN: filed|shipped|dropped — <why>` tombstones. Never push, tag, release or publish without Lionel.
7. Session end is hook-gated: if `CLAUDE.md`, `refs/` or `.claude/` changed since the last `harness-audit:` commit, run the scoped audit (`refs/harness/INDEX.md`) and commit the marker (`--allow-empty` if clean).

## Working doctrine

- Finish forward: improvements found on task are part of it, and finishing sweeps the consequences. Complete and consistent, not maximal — speculative polish against unstable facts stays unbuilt.
- File instead only when the work is no longer the task you are on: a different track, not a bigger one. Harness work found in session stays in session.
- Defer only on a named trigger: a missing external fact, a sign-off pending as a PLAN.md ticket, or observed evidence. Never for effort; "needs Lionel" is not a trigger. No TODOs — a deferral is a ticket, a Queue entry, or it dies.
- Verify before done: `just quality` passes, plus the check named for the surface you touched (`refs/eng/INDEX.md` §Workflow; `deploy.md` for release and hosting). Show the command and what it returned, never an assertion that it works.
- Independent agent review before commit, via the Agent tool, and for `/ticket` advisors: bot code, constitutional docs, `ansible/`, `.github/workflows/`, `.claude/hooks/` and its `settings.json` wiring. Exempt: tombstones, plan bookkeeping, `ansible/README.md` prose, non-constitutional refs fixes. The exemption covers the bookkeeping, not the commit carrying it: a tombstone that also writes a constraint into a reviewed path is reviewed for that write.
- Style: KISS, local, DRY, short. No narration comments, no explanation-in-code, no patterns added for human readability. Reports lead with the answer, then the evidence — never the search that found it. Length is earned by content, not thoroughness on display.
- Tech claims: current docs first (context7), never training-data recall. A failed fetch is not an absence — follow cross-host redirects, read the whole raw page, and record "unverified", never "undocumented".
- Game-domain claims: the `vtes` skill, never recall.

## Approval tiers

- **Routine**: lands when the work is done — after `/ticket` grilling if it was filed, in session otherwise.
- **Strategic**, needs Lionel: new user-facing command or surface, dependency/runtime-floor changes, hosting or release-process changes, any push to the public repo including an incidental one, meaning-changes to constitutional docs (project facts, Working doctrine, plan format). Filed work waits at `awaiting-sign-off`; in-session work takes a live sign-off recorded in the commit, and without Lionel it stops and becomes a ticket. Meaning-preserving edits to constitutional docs are routine; their review must confirm zero drift.

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
