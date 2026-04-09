#!/usr/bin/env bash
# Stop hook — extracts <!-- buddy: ... --> comments from assistant messages.
# These invisible HTML comments are written by Claude when contextually appropriate.
# Cooldown: 2 seconds (must match COOLDOWNS["buddy-comment"] in reactions.py).

set -euo pipefail

# shellcheck source=lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"

COOLDOWN_SECS=2

check_cooldown "$CODECRITTER_DIR/.last_comment" "$COOLDOWN_SECS" || exit 0

# ── Read last assistant message from stdin ──────────────────────────
INPUT=$(cat)
MSG=$(echo "$INPUT" | "$PYTHON" -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('last_assistant_message', ''))
except:
    pass
" 2>/dev/null || true)

if [[ -z "$MSG" ]]; then
    exit 0
fi

# ── Extract <!-- buddy: ... --> comment ─────────────────────────────
COMMENT=$(echo "$MSG" | grep -oP '<!--\s*buddy:\s*\K.+?(?=\s*-->)' | tail -1 || true)

if [[ -z "$COMMENT" ]]; then
    exit 0
fi

# ── Set reaction ───────────────────────────────────────────────────
PYTHONPATH="$PYTHONPATH" "$PYTHON" -m codecritter buddy-comment --text "$COMMENT" 2>/dev/null &
exit 0
