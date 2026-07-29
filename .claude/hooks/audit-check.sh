#!/bin/bash
# Stop hook: blocks session end when harness files changed since the last 'harness-audit:' commit.
input=$(cat)
printf '%s' "$input" | grep -q '"stop_hook_active": *true' && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
last=$(git log -1 --format=%H --grep='^harness-audit:' 2>/dev/null)
changed=$(
  { [ -n "$last" ] && git diff --name-only "$last"..HEAD -- CLAUDE.md refs .claude
    git status --porcelain -uall -- CLAUDE.md refs .claude | awk '{print $NF}'
  } 2>/dev/null | sort -u
)
[ -n "$last" ] && [ -z "$changed" ] && exit 0
scope=$(printf '%s\n' "$changed" | cut -d/ -f1-2 | sort -u | tr '\n' ' ')
[ -z "${scope// /}" ] && scope='CLAUDE.md refs .claude (no audit marker yet)'
printf 'Harness audit owed. Changed since last audit: %s\n' "$scope" >&2
printf 'Sweep per refs/harness/INDEX.md, then commit "harness-audit: <scope>" (--allow-empty if clean). Full-tree if CLAUDE.md or a constitutional doc is in that list, scoped otherwise. Fires again at the next turn end until the marker lands, so if an audit is already running this is not a second request. It does NOT fire on a turn that is itself continuing from this block (stop_hook_active), so the block is a reminder, not a seal.\n' >&2
exit 2
