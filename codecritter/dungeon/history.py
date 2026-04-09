"""Dungeon run history, playstyle tracking, and meta-progression."""

from __future__ import annotations

import time
from collections import Counter


def empty_history() -> dict:
    """Return a fresh dungeon_history structure."""
    return {
        "deaths": [],
        "runs": [],
        "playstyle": {"attack": 0, "defend": 0, "flee": 0, "item": 0, "special": 0},
        "total_enemies_defeated": 0,
        "total_floors_cleared": 0,
        "total_runs": 0,
        "unlocks": {},
    }


def record_death(
    history: dict,
    enemy_id: str,
    enemy_name: str,
    floor: int,
    biome: str,
) -> None:
    """Record a death to history."""
    history["deaths"].append({
        "enemy_id": enemy_id,
        "enemy_name": enemy_name,
        "floor": floor,
        "biome": biome,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })


def record_run(
    history: dict,
    floors_cleared: int,
    biome: str,
    cause_of_death: str | None,
    gold_earned: int,
    enemies_defeated: int,
    extracted: bool,
) -> None:
    """Record a completed run (death, flee, or extraction-leave)."""
    history["runs"].append({
        "floors_cleared": floors_cleared,
        "biome": biome,
        "cause_of_death": cause_of_death,
        "gold_earned": gold_earned,
        "enemies_defeated": enemies_defeated,
        "extracted": extracted,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    history["total_runs"] += 1
    history["total_floors_cleared"] += floors_cleared
    history["total_enemies_defeated"] += enemies_defeated


def merge_action_counts(history: dict, action_counts: dict) -> None:
    """Merge per-run action counts into lifetime playstyle tracker."""
    for action, count in action_counts.items():
        if action in history["playstyle"]:
            history["playstyle"][action] += count


def get_taunts(history: dict, enemy_id: str) -> list[str]:
    """Get taunt messages if the player has died to this enemy before."""
    death_count = sum(1 for d in history["deaths"] if d["enemy_id"] == enemy_id)
    if death_count == 0:
        return []

    taunts = []
    if death_count == 1:
        taunts.append("This enemy remembers you... 'Back for more?'")
    elif death_count == 2:
        taunts.append("'We meet again. You haven't learned.'")
    else:
        taunts.append(f"'That's {death_count} times now. Impressive persistence.'")
    return taunts


def get_hints(history: dict, enemy_id: str, enemy_type: str) -> list[str]:
    """Get weakness hints if the player has died to this enemy type 3+ times."""
    type_deaths = sum(1 for d in history["deaths"] if d.get("enemy_id") == enemy_id)
    if type_deaths >= 3:
        from .types import SUPER_EFFECTIVE
        # Find what type is super effective against this enemy's type
        weak_to = [atk for atk, defn in SUPER_EFFECTIVE.items() if defn == enemy_type]
        if weak_to:
            return [f"Hint: This enemy is weak to {weak_to[0]}-type attacks!"]
    return []


def get_dominant_playstyle(history: dict) -> str | None:
    """Return the most-used action, or None if no data."""
    style = history.get("playstyle", {})
    total = sum(style.values())
    if total == 0:
        return None
    return max(style, key=style.get)  # type: ignore[arg-type]


def get_adapted_enemy_bias(history: dict) -> str | None:
    """Return an enemy trait to bias toward based on playstyle counter.

    Aggressive players (attack-heavy) face more defensive enemies.
    Defensive players face DoT/debuff enemies.
    Flee-heavy players face fast enemies.
    """
    dominant = get_dominant_playstyle(history)
    if dominant is None:
        return None

    counter_map = {
        "attack": "fortify",    # defensive enemies
        "defend": "grow",       # growing threats
        "flee": None,           # fast enemies (handled by speed, not special)
        "item": "corrupt",      # debuff enemies
        "special": "double_attack",  # punishing enemies
    }
    return counter_map.get(dominant)


def check_unlocks(history: dict, floors_cleared: int, boss_defeated: str | None, biome: str) -> list[str]:
    """Check and grant new unlocks. Returns list of newly unlocked ids."""
    unlocks = history["unlocks"]
    new = []

    # Floor milestones
    for milestone in [5, 10, 15, 20]:
        key = f"floor_{milestone}"
        if floors_cleared >= milestone and key not in unlocks:
            unlocks[key] = True
            new.append(key)

    # Boss defeats
    if boss_defeated:
        key = f"boss_{biome}"
        if key not in unlocks:
            unlocks[key] = True
            new.append(key)

    return new


def has_unlock(history: dict, unlock_id: str) -> bool:
    """Check if a specific unlock has been earned."""
    return history.get("unlocks", {}).get(unlock_id, False)
