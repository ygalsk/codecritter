"""Pre-render companion art frames for the statusline to consume.

The statusline (bash) reads ~/.claude/codecritter/art_cache.json instead of
maintaining its own hardcoded art.  species_art.py remains the single
source of truth.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import CodecritterState
from .species_art import HAT_ART, get_frames

CACHE_FILE = Path.home() / ".claude" / "codecritter" / "art_cache.json"


def _art_fingerprint(state: CodecritterState) -> tuple:
    spec = state.stats.highest() if state.stage == "adult" else None
    return (state.species.lower(), state.stage, state.eyes, state.hat, spec)


def _split_frame(frame: str) -> list[str]:
    """Split a multiline art string into lines, stripping leading/trailing blanks."""
    lines = frame.split("\n")
    # Strip leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    # Strip trailing blank lines
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def render_art_cache(state: CodecritterState) -> dict:
    """Build cache dict from current state using species_art.get_frames()."""
    species = state.species.lower()
    eyes = state.eyes or "\u00b7"
    spec = state.stats.highest() if state.stage == "adult" else None

    frames_raw = get_frames(species, state.stage, spec, eyes)
    frames = [_split_frame(f) for f in frames_raw]

    # Blink: replace eyes with "-"
    blink_raw = get_frames(species, state.stage, spec, "-")
    blink_frames = [_split_frame(f) for f in blink_raw]

    hat_line = HAT_ART.get(state.hat, "") if state.hat else ""

    return {
        "version": 1,
        "species": species,
        "stage": state.stage,
        "eyes": eyes,
        "hat": state.hat,
        "specialization": spec,
        "frames": frames,
        "blink_frames": blink_frames,
        "hat_line": hat_line,
    }


def write_art_cache(state: CodecritterState) -> None:
    """Write cache only if art-relevant fields changed."""
    fp = _art_fingerprint(state)

    # Check if cache is already up-to-date
    if CACHE_FILE.exists():
        try:
            existing = json.loads(CACHE_FILE.read_text())
            existing_fp = (
                existing.get("species"),
                existing.get("stage"),
                existing.get("eyes"),
                existing.get("hat"),
                existing.get("specialization"),
            )
            if existing_fp == fp:
                return
        except (json.JSONDecodeError, KeyError):
            pass

    data = render_art_cache(state)
    content = json.dumps(data, indent=2, ensure_ascii=False)

    # Atomic write
    cache_dir = CACHE_FILE.parent
    cache_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=cache_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, str(CACHE_FILE))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


if __name__ == "__main__":
    from . import persistence

    state = persistence.load_quiet()
    write_art_cache(state)
    print(f"Art cache written to {CACHE_FILE}")
