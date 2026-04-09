"""Type system for combat — 5-way stat-based type wheel.

Type effectiveness cycle:
  DEBUGGING → CHAOS → PATIENCE → SNARK → WISDOM → DEBUGGING
  (each beats the next, is weak to the previous)
"""

from __future__ import annotations

# The five combat types, matching Jamb's stats
TYPES = ("debugging", "chaos", "patience", "snark", "wisdom")

# Effectiveness: attacker_type -> set of types it's super effective against
SUPER_EFFECTIVE: dict[str, str] = {
    "debugging": "chaos",
    "chaos": "patience",
    "patience": "snark",
    "snark": "wisdom",
    "wisdom": "debugging",
}

# Multipliers
SUPER_EFFECTIVE_MULT = 1.5
RESISTED_MULT = 0.5
NEUTRAL_MULT = 1.0


def get_effectiveness(attacker_type: str | None, defender_type: str | None) -> float:
    """Return the damage multiplier for attacker vs defender type.

    Returns 1.5 (super effective), 0.5 (resisted), or 1.0 (neutral).
    If either type is None, returns neutral.
    """
    if not attacker_type or not defender_type:
        return NEUTRAL_MULT

    attacker_type = attacker_type.lower()
    defender_type = defender_type.lower()

    if SUPER_EFFECTIVE.get(attacker_type) == defender_type:
        return SUPER_EFFECTIVE_MULT

    if SUPER_EFFECTIVE.get(defender_type) == attacker_type:
        return RESISTED_MULT

    return NEUTRAL_MULT


def effectiveness_label(multiplier: float) -> str | None:
    """Return a display label for the effectiveness, or None if neutral."""
    if multiplier >= SUPER_EFFECTIVE_MULT:
        return "Super effective!"
    elif multiplier <= RESISTED_MULT:
        return "Not very effective..."
    return None
