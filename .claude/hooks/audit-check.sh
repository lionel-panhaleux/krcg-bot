#!/bin/bash
# Stop hook: blocks session end when harness files changed since the last 'harness-audit:' commit.
input=$(cat)
printf '%s' "$input" | grep -q '"stop_hook_active": *true' && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
last=$(git log -1 --format=%H --grep='^harness-audit:' 2>/dev/null)
if [ -n "$last" ]; then
  changed="$(git diff --name-only "$last"..HEAD -- CLAUDE.md refs .claude 2>/dev/null)$(git status --porcelain -- CLAUDE.md refs .claude 2>/dev/null)"
  [ -z "$changed" ] && exit 0
fi
echo "Harness files (CLAUDE.md, refs/, .claude/) changed since the last audit. Run the scoped harness audit (refs/harness/INDEX.md: changed subtree + pointers; full-tree if constitutional docs changed), then commit with a 'harness-audit: <scope>' marker (--allow-empty if clean)." >&2
exit 2
