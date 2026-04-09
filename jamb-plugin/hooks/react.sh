#!/usr/bin/env bash
# PostToolUse hook for Bash — detects errors, test failures, and large diffs.
# Triggers a Jamb reaction when patterns are found.
# Cooldown: 15 seconds (must match COOLDOWNS["error"] etc. in reactions.py).

set -euo pipefail

# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"

COOLDOWN_SECS=15

check_cooldown "$JAMB_DIR/.last_react" "$COOLDOWN_SECS" || exit 0

# ── Read tool result from stdin ─────────────────────────────────────
INPUT=$(cat)
TOOL_RESULT=$(echo "$INPUT" | "$PYTHON" -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_result', ''))
except:
    pass
" 2>/dev/null || true)

if [[ -z "$TOOL_RESULT" ]]; then
    exit 0
fi

# ── Pattern matching ────────────────────────────────────────────────
REASON=""

# Test failures
if echo "$TOOL_RESULT" | grep -qiP '\b[1-9][0-9]* (failed|failing)\b|tests? failed|^FAIL(ED)?|✗|✘'; then
    REASON="test-fail"
# Errors
elif echo "$TOOL_RESULT" | grep -qiP '\berror:|\bexception\b|\btraceback\b|\bpanicked at\b|\bfatal:|exit code [1-9]'; then
    REASON="error"
# Large diffs (>80 insertions)
elif echo "$TOOL_RESULT" | grep -qP '^\+.*[0-9]+ insertions'; then
    LINES=$(echo "$TOOL_RESULT" | grep -oP '[0-9]+(?= insertions)' | head -1)
    if [[ -n "$LINES" ]] && [[ "$LINES" -gt 80 ]]; then
        REASON="large-diff"
    fi
fi

if [[ -z "$REASON" ]]; then
    exit 0
fi

# ── Trigger reaction ───────────────────────────────────────────────
PYTHONPATH="$PYTHONPATH" "$PYTHON" -m jamb react --reason "$REASON" 2>/dev/null &
exit 0
