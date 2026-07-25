#!/bin/bash
# Stop hook: blocks session end while uncommitted code changes fail the quality gate.
input=$(cat)
printf '%s' "$input" | grep -q '"stop_hook_active": *true' && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -n "$(git status --porcelain -- src tests 2>/dev/null)" ] || exit 0
command -v just >/dev/null 2>&1 || exit 0
out=$(just quality 2>&1) && exit 0
printf 'Quality gate failed on uncommitted code changes — fix, then re-run `just quality`.\n%s\n' \
  "$(printf '%s' "$out" | tail -c 4000)" >&2
exit 2
