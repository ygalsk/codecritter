"""Enemy definitions for the Code Dungeon.

Thin dispatcher over data_loader — all content lives in JSON files.
"""

from __future__ import annotations

import copy

from . import data_loader


def enemies_for_floor(floor: int, biome: str = "generic") -> list[dict]:
    """Return enemies that can appear on this floor, with difficulty scaling."""
    data = data_loader.load_biome(biome)
    base = [e for e in data.get("enemies", []) if e.get("floor_min", 1) <= floor]
    return [_scale_enemy(dict(e), floor) for e in base]


def boss_for_floor(floor: int, biome: str = "generic") -> dict:
    """Return the boss for this floor number (1-indexed), with difficulty scaling."""
    data = data_loader.load_biome(biome)
    bosses = data.get("bosses", [])
    if not bosses:
        # Shouldn't happen, but fallback to generic
        data = data_loader.load_biome("generic")
        bosses = data.get("bosses", [])

    idx = min(floor - 1, len(bosses) - 1)
    boss = dict(bosses[idx])
    return _scale_enemy(boss, floor)


def _scale_enemy(enemy: dict, floor: int) -> dict:
    """Apply difficulty scaling based on floor number.

    HP +5/floor, ATK +1 per 2 floors, DEF +1 per 3 floors.
    Floor 1 gets no scaling.
    """
    if floor <= 1:
        return enemy

    extra_floors = floor - 1
    enemy["hp"] = enemy.get("hp", 20) + extra_floors * 5
    enemy["attack"] = enemy.get("attack", 5) + extra_floors // 2
    enemy["defense"] = enemy.get("defense", 2) + extra_floors // 3
    enemy["xp"] = enemy.get("xp", 8) + extra_floors * 2
    enemy["gold"] = enemy.get("gold", 5) + extra_floors

    return enemy


# ── Backwards compatibility ─────────────────────────────────────────
# Some code may still import these lists directly. Load them lazily
# from the generic biome.

def _get_generic_enemies() -> list[dict]:
    return data_loader.load_biome("generic").get("enemies", [])

def _get_generic_bosses() -> list[dict]:
    return data_loader.load_biome("generic").get("bosses", [])


class _LazyList:
    """List-like wrapper that loads data on first access."""
    def __init__(self, loader):
        self._loader = loader
        self._data = None

    def _ensure(self):
        if self._data is None:
            self._data = self._loader()

    def __iter__(self):
        self._ensure()
        return iter(self._data)

    def __len__(self):
        self._ensure()
        return len(self._data)

    def __getitem__(self, idx):
        self._ensure()
        return self._data[idx]


ENEMIES = _LazyList(_get_generic_enemies)
BOSSES = _LazyList(_get_generic_bosses)
