"""Hook handlers — Python replacements for react.sh and buddy-comment.sh.

These read JSON from stdin (the hook payload) and trigger reactions
without needing shell scripts or hardcoded paths.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

CODECRITTER_DIR = Path.home() / ".claude" / "codecritter"


def _check_cooldown(cooldown_file: Path, seconds: float) -> bool:
    """Return True if enough time has elapsed since last trigger."""
    now = time.time()
    if cooldown_file.exists():
        try:
            last = float(cooldown_file.read_text().strip())
            if now - last < seconds:
                return False
        except (ValueError, OSError):
            pass
    CODECRITTER_DIR.mkdir(parents=True, exist_ok=True)
    cooldown_file.write_text(str(int(now)))
    return True


def _read_stdin_json() -> dict:
    """Read JSON from stdin, return empty dict on failure."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def handle_react() -> None:
    """PostToolUse hook for Bash — detect errors, test failures, large diffs."""
    cooldown_file = CODECRITTER_DIR / ".last_react"
    if not _check_cooldown(cooldown_file, 15):
        return

    data = _read_stdin_json()
    tool_result = data.get("tool_result", "")
    if not tool_result:
        return

    reason = ""

    # Test failures
    if re.search(
        r"\b[1-9][0-9]* (failed|failing)\b|tests? failed|^FAIL(ED)?|✗|✘",
        tool_result,
        re.IGNORECASE | re.MULTILINE,
    ):
        reason = "test-fail"
    # Errors
    elif re.search(
        r"\berror:|\bexception\b|\btraceback\b|\bpanicked at\b|\bfatal:|exit code [1-9]",
        tool_result,
        re.IGNORECASE,
    ):
        reason = "error"
    # Large diffs (>80 insertions)
    elif m := re.search(r"(\d+) insertions", tool_result):
        if int(m.group(1)) > 80:
            reason = "large-diff"

    if not reason:
        return

    from . import persistence
    from .reactions import pick_reaction, set_reaction

    state = persistence.load_quiet()
    text = pick_reaction(state.species, reason)
    if set_reaction(state, text, reason):
        persistence.save(state)


def handle_comment() -> None:
    """Stop hook — extract <!-- buddy: ... --> comments from assistant messages."""
    cooldown_file = CODECRITTER_DIR / ".last_comment"
    if not _check_cooldown(cooldown_file, 20):
        return

    data = _read_stdin_json()
    msg = data.get("last_assistant_message", "")
    if not msg:
        return

    match = re.search(r"<!--\s*buddy:\s*(.+?)\s*-->", msg)
    if not match:
        return

    comment = match.group(1)

    from . import persistence
    from .reactions import set_reaction

    state = persistence.load_quiet()
    if set_reaction(state, comment, "buddy-comment"):
        persistence.save(state)
