#!/usr/bin/env bash
# Shared utilities for Jamb hooks.

# Derive paths from the hook's location rather than hardcoding
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
JAMB_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"
JAMB_DIR="$HOME/.claude/jamb"
PYTHONPATH="$JAMB_ROOT"
PYTHON="python3"

# check_cooldown FILE SECONDS
# Returns 0 (pass) if enough time has elapsed, 1 (fail) if still in cooldown.
# On pass, writes the current timestamp to FILE.
check_cooldown() {
    local file="$1" secs="$2"
    local now
    now=$(date +%s)
    if [[ -f "$file" ]]; then
        local last
        last=$(cat "$file" 2>/dev/null || echo 0)
        if (( now - last < secs )); then
            return 1
        fi
    fi
    echo "$now" > "$file"
    return 0
}
