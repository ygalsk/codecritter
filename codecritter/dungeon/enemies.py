"""Enemy definitions for the Code Dungeon.

Thin dispatcher over data_loader — all content lives in JSON files.
"""

from __future__ import annotations

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

    Multiplicative scaling: 15% per floor for combat stats.
    Additive scaling for XP/gold rewards.
    Floor 1 gets no scaling.
    """
    if floor <= 1:
        return enemy

    extra_floors = floor - 1
    scale = 1 + 0.15 * extra_floors
    enemy["hp"] = int(enemy.get("hp", 20) * scale)
    enemy["attack"] = int(enemy.get("attack", 5) * scale)
    enemy["defense"] = int(enemy.get("defense", 2) * scale)
    enemy["xp"] = enemy.get("xp", 8) + extra_floors * 2
    enemy["gold"] = enemy.get("gold", 5) + extra_floors

    return enemy
