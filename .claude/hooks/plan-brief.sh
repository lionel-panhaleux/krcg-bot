#!/bin/bash
# SessionStart hook: surfaces the active plan so the main session starts with it in context.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -f PLAN.md ] || exit 0
now=$(awk '/^## Now/{f=1;next} /^## /{f=0} f' PLAN.md | grep -v '^[[:space:]]*$' | grep -v '^(empty)$')
signoff=$(grep -F -- ' — awaiting-sign-off — ' PLAN.md)
[ -z "$now$signoff" ] && exit 0
echo "PLAN.md — Now:"
[ -n "$now" ] && echo "$now"
[ -n "$signoff" ] && printf 'Awaiting Lionel sign-off (surface these first, not workable until signed):\n%s\n' "$signoff"
exit 0
