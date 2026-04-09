"""Data-driven content loader for the dungeon system.

Reads game content from JSON files under codecritter/dungeon/data/.
Caches loaded data per process — load once, use everywhere.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent / "data"

# ── Caches ──────────────────────────────────────────────────────────

_biome_cache: dict[str, dict] = {}
_items_cache: dict[str, Any] | None = None
_modifiers_cache: list[dict] | None = None

# ── Required keys for light validation ──────────────────────────────

_ENEMY_REQUIRED = {"id", "name", "hp", "attack", "defense", "speed", "xp", "gold", "type", "floor_min"}
_BOSS_REQUIRED = _ENEMY_REQUIRED
_ITEM_REQUIRED = {"id", "name", "type"}
_TRAP_REQUIRED = {"id", "name", "damage_range"}
_MODIFIER_REQUIRED = {"id", "name", "effects"}


def _validate_entries(entries: list[dict], required: set[str], label: str) -> None:
    """Log warnings for entries missing required keys."""
    for entry in entries:
        missing = required - entry.keys()
        if missing:
            log.warning("%s '%s' missing keys: %s", label, entry.get("id", "?"), missing)


# ── Public API ──────────────────────────────────────────────────────

def load_biome(biome_id: str) -> dict:
    """Load and cache a biome definition by id. Falls back to generic."""
    if biome_id in _biome_cache:
        return _biome_cache[biome_id]

    path = _DATA_DIR / "biomes" / f"{biome_id}.json"
    if not path.exists():
        log.warning("Biome file not found: %s — falling back to generic", path)
        if biome_id != "generic":
            return load_biome("generic")
        raise FileNotFoundError(f"Generic biome file missing: {path}")

    with open(path) as f:
        data = json.load(f)

    # Light validation
    _validate_entries(data.get("enemies", []), _ENEMY_REQUIRED, "Enemy")
    _validate_entries(data.get("bosses", []), _BOSS_REQUIRED, "Boss")
    _validate_entries(data.get("traps", []), _TRAP_REQUIRED, "Trap")

    _biome_cache[biome_id] = data
    return data


def load_items() -> dict:
    """Load and cache all item definitions. Returns the full items dict."""
    global _items_cache
    if _items_cache is not None:
        return _items_cache

    path = _DATA_DIR / "items.json"
    with open(path) as f:
        data = json.load(f)

    all_items = (
        data.get("weapons", [])
        + data.get("armors", [])
        + data.get("accessories", [])
        + data.get("consumables", [])
    )
    _validate_entries(all_items, _ITEM_REQUIRED, "Item")

    # Build lookup indices
    data["_all"] = all_items
    data["_by_id"] = {item["id"]: item for item in all_items}
    data["_by_rarity"] = {}
    for item in all_items:
        rarity = item.get("rarity", "common")
        data["_by_rarity"].setdefault(rarity, []).append(item)

    _items_cache = data
    return data


def load_floor_modifiers() -> list[dict]:
    """Load and cache floor modifier definitions."""
    global _modifiers_cache
    if _modifiers_cache is not None:
        return _modifiers_cache

    path = _DATA_DIR / "floor_modifiers.json"
    with open(path) as f:
        data = json.load(f)

    _validate_entries(data, _MODIFIER_REQUIRED, "FloorModifier")
    _modifiers_cache = data
    return data


def get_item(item_id: str) -> dict | None:
    """Look up a single item by id."""
    items = load_items()
    return items["_by_id"].get(item_id)


def get_items_by_id() -> dict[str, dict]:
    """Get the full id→item lookup dict."""
    return load_items()["_by_id"]


def get_items_by_rarity(rarity: str) -> list[dict]:
    """Get all items of a given rarity."""
    return load_items()["_by_rarity"].get(rarity, [])


def get_all_items() -> list[dict]:
    """Get flat list of all items."""
    return load_items()["_all"]


def clear_cache() -> None:
    """Clear all caches. Useful for testing."""
    global _items_cache, _modifiers_cache
    _biome_cache.clear()
    _items_cache = None
    _modifiers_cache = None
