# Platform facts

Claude Code behaviour the harness depends on. External reality: verify against current docs before relying on a line, and re-verify on audit. Sources: `code.claude.com/docs/en/{sub-agents,skills,memory,hooks,features-overview}`, checked 2026-07-25.

## What a subagent actually gets
- Its own markdown body as system prompt, plus environment details — NOT the main Claude Code system prompt.
- The full CLAUDE.md hierarchy and a git-status snapshot. Only the built-in `Explore` and `Plan` agents skip them. So every line of `CLAUDE.md` is paid again on every spawn.
- Preloaded skills named in a `skills:` frontmatter field, in full. Unlisted skills stay reachable through the `Skill` tool.
- Nothing else: no conversation history, no files the main session read, no auto memory, no output style.

## Tool filters that shape agent design
- Never available to a subagent: `AskUserQuestion`, `EnterPlanMode`, `ScheduleWakeup`, `Workflow`, `TaskOutput`. This is why `/ticket` grills from the main loop only.
- `Agent` is withheld unless `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is set — subagents cannot delegate by default.
- Subagents run in the background by default, and a background subagent keeps only: Read, Grep, Glob, Bash, Edit, Write, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, SendMessage, Monitor, TaskStop, Artifact, NotebookEdit, EnterWorktree/ExitWorktree, plus every MCP tool. Anything else in a `tools:` list silently disappears in the background.

## Mechanism selection
| Need | Mechanism |
|---|---|
| True every session, every agent | `CLAUDE.md` (target <200 lines; it is re-paid per subagent) |
| True only when touching certain files | `.claude/rules/*.md` with `paths:` frontmatter — loads on match |
| Pulled when a task needs it | `refs/` behind an INDEX, or a skill |
| A procedure with steps | Skill. Its rendered body stays in context for the rest of the session — write standing instructions, not one-shot narration |
| Must happen regardless of what the model decides | Hook. An instruction is a request; a hook is enforcement |
| Verbose work whose result is a summary | Subagent |

## Hook semantics relied on here
- Hooks in `settings.json` are NOT picked up mid-session: the session that edits a hook does not run it. Restart or `/reload-project`.
- `Stop` hook exit 2 blocks the turn from ending and feeds stderr back to the model. Claude Code overrides the hook after 8 consecutive blocks — the gate is strong, not absolute.
- `stop_hook_active: true` in the hook's stdin means a Stop hook is already running; every Stop hook here exits 0 on it to avoid a loop.
- `SessionStart` stdout on exit 0 is added to the session — that is how `plan-brief.sh` injects the plan without model effort.
- Exit 1 is a non-blocking error, not a failure. Only 2 blocks.

## Auto memory
On by default, machine-local, at `~/.claude/projects/<project>/memory/`, loaded every session, and invisible to `refs/` audits. It is a second home for facts this harness insists on keeping in one place — see the `CLAUDE.md` rule. Set `"autoMemoryEnabled": false` in `.claude/settings.json` if the coordination rule proves insufficient.
