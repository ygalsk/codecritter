from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from .art_cache import write_art_cache
from .models import CodecritterState

SAVE_DIR = Path.home() / ".claude" / "codecritter"
SAVE_FILE = SAVE_DIR / "save.json"
SAVE_VERSION = 1

OLD_SAVE_DIR = Path.home() / ".claude" / "jamb"


def _migrate_save_dir():
    """One-time migration from ~/.claude/jamb to ~/.claude/codecritter."""
    if OLD_SAVE_DIR.exists() and not SAVE_DIR.exists():
        shutil.copytree(OLD_SAVE_DIR, SAVE_DIR)


def load_quiet() -> CodecritterState:
    """Load state without starting a session (no decay, no session increment)."""
    _migrate_save_dir()
    if SAVE_FILE.exists():
        try:
            data = json.loads(SAVE_FILE.read_text())
            return CodecritterState.from_dict(data.get("codecritter", data.get("jamb", {})))
        except (json.JSONDecodeError, KeyError):
            pass
    return CodecritterState()


def load() -> CodecritterState:
    state = load_quiet()
    state.start_session()
    return state


def save(state: CodecritterState) -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"version": SAVE_VERSION, "codecritter": state.as_dict()}
    content = json.dumps(data, indent=2)
    # Atomic write: write to temp file then rename to prevent corruption
    # from concurrent writes (hooks + TUI writing simultaneously).
    fd, tmp_path = tempfile.mkstemp(dir=SAVE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, str(SAVE_FILE))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    # Update art cache if art-relevant fields changed (cheap no-op otherwise)
    try:
        write_art_cache(state)
    except Exception:
        pass  # non-critical — statusline degrades gracefully
