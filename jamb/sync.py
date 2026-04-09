"""Bidirectional sync between native Claude Code buddy and Jamb TUI.

Native → TUI:  Pull rarity and base stats from bones into save.json.
TUI → Native:  Push trained stats, level, mood into .claude.json personality.
"""

from __future__ import annotations

import json
from pathlib import Path

from .bones import get_native_bones, RARITY_STAR_MAP
from .models import JambState

CLAUDE_JSON = Path.home() / ".claude.json"


def sync_bones_to_tui(state: JambState) -> bool:
    """Pull native bones (rarity, base stats) into TUI state.

    On first sync, scales native base stats (0-100) to the TUI's 0-255 range
    and uses them to seed starting values. On subsequent syncs, only updates
    native_rarity and native_stats fields (doesn't overwrite trained stats).

    Returns True if bones were synced, False if unavailable.
    """
    bones = get_native_bones()
    if not bones:
        return False

    state.native_rarity = bones["rarity"]
    state.native_stats = bones["stats"]
    state.rarity = bones["rarity_display"]
    state.species = bones["species"].title()  # "duck" -> "Duck"
    state.eyes = bones["eyes"]
    state.hat = bones["hat"]
    state.shiny = bones["shiny"]

    if not state.bones_synced:
        # First sync: seed TUI stats from native base stats
        # Scale 0-100 → proportional position in 0-255 range
        for stat_name, base_val in bones["stats"].items():
            current = getattr(state.stats, stat_name, 0)
            scaled = int(base_val * 2.55)  # 0-100 → 0-255
            # Only seed if TUI stat is still at or near default
            if current <= scaled:
                state.stats.add(stat_name, scaled - current, state.stat_cap())

    state.bones_synced = True
    return True


def sync_tui_to_native(state: JambState) -> bool:
    """Push TUI progression into native .claude.json companion personality.

    Updates the personality field to include level, title, trained stats,
    mood, and notable achievements. This gets picked up by:
    - The companion_intro system prompt injection
    - The buddy_react API (speech bubbles)
    - The /buddy card display

    Returns True if synced, False on error.
    """
    if not CLAUDE_JSON.exists():
        return False

    try:
        data = json.loads(CLAUDE_JSON.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    companion = data.get("companion")
    if not companion:
        return False

    # Build the enriched personality
    personality = _build_enriched_personality(state, companion)
    companion["personality"] = personality

    # Write back atomically
    try:
        content = json.dumps(data, indent=2)
        CLAUDE_JSON.write_text(content)
    except OSError:
        return False

    return True


def _build_enriched_personality(state: JambState, companion: dict) -> str:
    """Build a rich personality string that encodes TUI progression."""
    # Extract the original personality (before any TUI enrichment)
    raw = companion.get("personality", "")
    # Strip any previous TUI progression block
    marker = "\n\n[Jamb Training Data]"
    if marker in raw:
        raw = raw[: raw.index(marker)]

    stats = state.stats.as_dict()
    highest = state.stats.highest()
    highest_val = stats[highest]

    # Equipment summary
    weapon = state.equipment.get("weapon", "none")
    armor = state.equipment.get("armor", "none")

    progression = (
        f"{marker}\n"
        f"Level {state.level} {state.title} ({state.rarity}). "
        f"Dominant stat: {highest.upper()} ({highest_val}/255). "
        f"Stats: "
        + ", ".join(f"{k.upper()}:{v}" for k, v in stats.items())
        + f". "
        f"Dungeon floor record: {state.dungeon_highest_floor}. "
        f"Equipment: {weapon}/{armor}. "
        f"Gold: {state.gold}."
    )

    return raw + progression


def full_sync(state: JambState) -> dict[str, bool]:
    """Run both sync directions. Returns status of each."""
    return {
        "bones_to_tui": sync_bones_to_tui(state),
        "tui_to_native": sync_tui_to_native(state),
    }
