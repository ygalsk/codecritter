"""Compute native Claude Code buddy bones from account UUID.

The native /buddy system generates companion traits deterministically from
the user's organization UUID using FNV-1a hashing + Mulberry32 PRNG.
Bones (species, rarity, stats, eyes, hat, shiny) are never persisted —
recomputed in-memory every session.  This module replicates that algorithm
so the Jamb TUI can know its native rarity and base stats.
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────

CLAUDE_JSON = Path.home() / ".claude.json"
SALT = "friend-2026-0401"

SPECIES = [
    "duck", "goose", "blob", "cat", "dragon", "octopus", "owl", "penguin",
    "turtle", "snail", "ghost", "axolotl", "capybara", "cactus", "robot",
    "rabbit", "mushroom", "chonk",
]

RARITY_WEIGHTS: list[tuple[float, str]] = [
    (0.60, "Common"),
    (0.25, "Uncommon"),
    (0.10, "Rare"),
    (0.04, "Epic"),
    (0.01, "Legendary"),
]

RARITY_STAR_MAP = {
    "Common": "★ COMMON",
    "Uncommon": "★★ UNCOMMON",
    "Rare": "★★★ RARE",
    "Epic": "★★★★ EPIC",
    "Legendary": "★★★★★ LEGENDARY",
}

STAT_FLOORS = {
    "Common": 5,
    "Uncommon": 15,
    "Rare": 25,
    "Epic": 35,
    "Legendary": 50,
}

STAT_PEAKS = {
    "Common": (55, 84),
    "Uncommon": (65, 94),
    "Rare": (75, 100),
    "Epic": (85, 100),
    "Legendary": (100, 100),
}

STAT_NAMES = ["debugging", "patience", "chaos", "wisdom", "snark"]

EYE_STYLES = ["·", "✦", "x", "◉", "@", "°"]

HATS_BY_RARITY = {
    "Common": [None],
    "Uncommon": [None, "crown", "tophat", "propeller"],
    "Rare": [None, "halo", "wizard"],
    "Epic": [None, "beanie"],
    "Legendary": [None, "tinyduck"],
}


# ── FNV-1a Hash ──────────────────────────────────────────────────────

def fnv1a(data: str) -> int:
    """FNV-1a 32-bit hash, matching the JS implementation."""
    h = 2166136261
    for ch in data:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


# ── Mulberry32 PRNG ──────────────────────────────────────────────────

class Mulberry32:
    """Deterministic 32-bit PRNG matching the JS implementation."""

    def __init__(self, seed: int) -> None:
        self._state = seed & 0xFFFFFFFF

    def next_float(self) -> float:
        self._state = (self._state + 0x6D2B79F5) & 0xFFFFFFFF
        t = self._state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = (t ^ ((t ^ (t >> 7)) * (t | 61))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 0x100000000

    def next_int(self, n: int) -> int:
        """Random integer in [0, n)."""
        return int(self.next_float() * n)


# ── Bone Generation ──────────────────────────────────────────────────

def _pick_weighted(rng: Mulberry32, weights: list[tuple[float, str]]) -> str:
    r = rng.next_float()
    cumulative = 0.0
    for weight, name in weights:
        cumulative += weight
        if r < cumulative:
            return name
    return weights[-1][1]


def _roll_stats(rng: Mulberry32, rarity: str) -> dict[str, int]:
    """Generate 5 stats: one peak, one dump, three mid-range."""
    floor = STAT_FLOORS[rarity]
    peak_lo, peak_hi = STAT_PEAKS[rarity]

    # Pick peak and dump stat indices
    peak_idx = rng.next_int(5)
    dump_idx = rng.next_int(4)
    if dump_idx >= peak_idx:
        dump_idx += 1

    stats = {}
    for i, name in enumerate(STAT_NAMES):
        if i == peak_idx:
            stats[name] = peak_lo + int(rng.next_float() * (peak_hi - peak_lo + 1))
        elif i == dump_idx:
            stats[name] = floor + int(rng.next_float() * 10)
        else:
            mid_lo = floor + 10
            mid_hi = peak_lo - 1
            if mid_hi <= mid_lo:
                mid_hi = mid_lo + 10
            stats[name] = mid_lo + int(rng.next_float() * (mid_hi - mid_lo + 1))

    return stats


def roll(org_uuid: str) -> dict:
    """Generate native bones from an organization UUID.

    Returns dict with: species, rarity, rarity_display, eyes, hat, shiny, stats
    """
    seed = fnv1a(org_uuid + SALT)
    rng = Mulberry32(seed)

    species = SPECIES[rng.next_int(len(SPECIES))]
    rarity = _pick_weighted(rng, RARITY_WEIGHTS)
    eyes = EYE_STYLES[rng.next_int(len(EYE_STYLES))]
    hat_pool = HATS_BY_RARITY.get(rarity, [None])
    hat = hat_pool[rng.next_int(len(hat_pool))]
    stats = _roll_stats(rng, rarity)
    shiny = rng.next_float() < 0.01

    return {
        "species": species,
        "rarity": rarity,
        "rarity_display": RARITY_STAR_MAP.get(rarity, rarity),
        "eyes": eyes,
        "hat": hat,
        "shiny": shiny,
        "stats": stats,
    }


# ── Read org UUID from ~/.claude.json ────────────────────────────────

def get_org_uuid() -> str | None:
    """Extract organizationUuid from ~/.claude.json."""
    if not CLAUDE_JSON.exists():
        return None
    try:
        data = json.loads(CLAUDE_JSON.read_text())
        return data.get("oauthAccount", {}).get("organizationUuid")
    except (json.JSONDecodeError, KeyError):
        return None


def get_native_bones() -> dict | None:
    """Compute native bones for the current user. Returns None if UUID unavailable."""
    org_uuid = get_org_uuid()
    if not org_uuid:
        return None
    return roll(org_uuid)
