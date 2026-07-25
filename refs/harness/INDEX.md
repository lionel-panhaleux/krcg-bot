# refs/harness

Scope: the harness itself — agents, skills, refs, CLAUDE.md, plan format.

Platform behaviour this all rests on — subagent context, tool filters, hook semantics, mechanism-selection table: `platform.md`. Read it before designing anything new.

## Conventions
- Agent defs ≤40 lines; loaded wholesale per spawn.
- Knowledge pull-based: `refs/<agent>/INDEX.md` first, sub-docs on demand.
- One fact one home; point, never restate.
- Delete, don't archive; git is history.
- No knowledge docs inside `.claude/agents/` — every `.md` there is an agent def.
- Product and domain knowledge that is true of the codebase belongs in the code or in `refs/`, never in both.
- Pick the mechanism by when the knowledge must be live, not by how important it feels (`platform.md` §Mechanism selection). A constraint that must hold while editing a file is a path-scoped rule, not a refs line someone has to remember to read; a rule that must hold regardless of judgement is a hook, not prose.
- Audit scope: changed subtree + everything pointing at it; full-tree when constitutional docs (project facts, Working doctrine, plan format) or CLAUDE.md changed, or on explicit call. Mark completion with a `harness-audit: <scope>` commit (`--allow-empty` if clean); the Stop hook (`.claude/hooks/audit-check.sh`) blocks session end until marked.

## Review checklist (run on audit)
1. Any agent def >40 lines, holding knowledge, or duplicating `refs/shared/project.md` facts?
2. Any refs doc stale vs `decisions.md` or vs the code it describes, orphaned, or pointing to a missing file?
3. Refs sub-docs unreferenced by their INDEX — or INDEX entries pointing to missing files?
4. Does the `/ticket` procedure still match `plan-format.md` and the CLAUDE.md tiers?
5. PLAN.md: dead lines (deleted tickets), counter drift, entries that bypassed `/ticket`?
6. `decisions.md`: lines already embodied in operative docs (delete, citing the home) — or standing constraints silently dropped since last audit?
7. `platform.md`: any line contradicted by current docs, or a harness mechanism relying on behaviour no longer documented?
8. Pre-existing rot = a finding that survived a prior completed audit covering its subtree (audit leak) or whose origin never tripped the trigger (trigger leak: unwatched path, or no originating commit — external-reality staleness). Fix it and note the leak class; a repeated unwatched-path leak means widening the hook's path filter.
