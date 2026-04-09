"""Shop rotation logic — daily rotating stock with level-gated tiers."""

from __future__ import annotations

import random
from datetime import datetime

# All possible shop items organized by tier
# Tier 1: Level 1+, Tier 2: Level 5+, Tier 3: Level 10+

SHOP_POOL: list[dict] = [
    # === TIER 1 — Stat boosters ===
    {"id": "debug_manual", "name": "Debugging Manual", "type": "stat_boost", "rarity": "uncommon", "boost_stat": "debugging", "boost_amount": 5, "price": 50, "description": "A thick book of debugging techniques. +5 DEBUGGING permanently.", "tier": 1, "category": "boost"},
    {"id": "meditation_cd", "name": "Meditation CD", "type": "stat_boost", "rarity": "uncommon", "boost_stat": "patience", "boost_amount": 5, "price": 50, "description": "Whale sounds and refactoring tips. +5 PATIENCE permanently.", "tier": 1, "category": "boost"},
    {"id": "chaos_dice", "name": "Chaos Dice", "type": "stat_boost", "rarity": "uncommon", "boost_stat": "chaos", "boost_amount": 5, "price": 50, "description": "Roll them and something random happens. +5 CHAOS permanently.", "tier": 1, "category": "boost"},
    {"id": "wisdom_scroll", "name": "Ancient Scroll", "type": "stat_boost", "rarity": "uncommon", "boost_stat": "wisdom", "boost_amount": 5, "price": 50, "description": "Contains forbidden knowledge about semicolons. +5 WISDOM permanently.", "tier": 1, "category": "boost"},
    {"id": "joke_book", "name": "1001 Dev Jokes", "type": "stat_boost", "rarity": "uncommon", "boost_stat": "snark", "boost_amount": 5, "price": 50, "description": "'Why do programmers hate nature? Too many bugs.' +5 SNARK permanently.", "tier": 1, "category": "boost"},

    # === TIER 1 — Consumables ===
    {"id": "coffee", "name": "Coffee Potion", "type": "consumable", "rarity": "common", "heal": 20, "price": 8, "description": "Hot, dark, and fixes everything temporarily.", "tier": 1, "category": "consumable"},
    {"id": "energy_drink", "name": "Energy Drink", "type": "consumable", "rarity": "common", "heal": 40, "price": 15, "description": "Pure liquid productivity.", "tier": 1, "category": "consumable"},

    # === TIER 1 — XP ===
    {"id": "xp_scroll", "name": "XP Scroll", "type": "xp_boost", "rarity": "uncommon", "xp_amount": 30, "price": 35, "description": "A compressed knowledge dump. +30 XP instantly.", "tier": 1, "category": "boost"},

    # === TIER 2 — Better consumables ===
    {"id": "sudo_potion", "name": "Sudo Potion", "type": "consumable", "rarity": "rare", "full_heal": True, "price": 50, "description": "With great power comes great restoration.", "tier": 2, "category": "consumable"},
    {"id": "code_review_scroll", "name": "Code Review Scroll", "type": "consumable", "rarity": "uncommon", "attack_buff": 5, "turns": 3, "price": 20, "description": "Reveals weaknesses in any codebase... or enemy.", "tier": 2, "category": "consumable"},

    # === TIER 2 — Backpack upgrades ===
    {"id": "backpack_upgrade_1", "name": "Bigger Backpack", "type": "backpack", "rarity": "rare", "capacity_to": 20, "price": 1000, "description": "Expands inventory to 20 slots.", "tier": 2, "category": "upgrade"},
    {"id": "xp_tome", "name": "XP Tome", "type": "xp_boost", "rarity": "rare", "xp_amount": 75, "price": 70, "description": "A massive tome of accumulated wisdom. +75 XP instantly.", "tier": 2, "category": "boost"},

    # === TIER 2 — Equipment ===
    {"id": "type_chart_scroll", "name": "Type Chart Scroll", "type": "consumable", "rarity": "uncommon", "price": 25, "description": "Shows enemy type weaknesses for 1 fight. Knowledge is power.", "tier": 2, "category": "consumable"},

    # === TIER 3 — Rare gear and top consumables ===
    {"id": "rollback_scroll", "name": "Rollback Scroll", "type": "consumable", "rarity": "rare", "revive": True, "price": 60, "description": "Reverts to last known good state.", "tier": 3, "category": "consumable"},
    {"id": "backpack_upgrade_2", "name": "Huge Backpack", "type": "backpack", "rarity": "legendary", "capacity_to": 25, "price": 3000, "description": "Expands inventory to 25 slots.", "tier": 3, "category": "upgrade"},
]


def max_tier_for_level(level: int) -> int:
    """Return the highest shop tier unlocked at this level."""
    if level >= 10:
        return 3
    if level >= 5:
        return 2
    return 1


def generate_daily_shop(level: int, date: str | None = None) -> list[dict]:
    """Generate the daily shop rotation.

    Returns 6 items:
    - 2 consumable items
    - 2 boosters/equipment
    - 1 guaranteed rare+ slot
    - 1 wild card from any category

    Uses date as seed for deterministic daily rotation.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    tier = max_tier_for_level(level)
    rng = random.Random(date)

    eligible = [item for item in SHOP_POOL if item["tier"] <= tier]

    # Split into pools
    consumables = [i for i in eligible if i["category"] == "consumable"]
    boosters = [i for i in eligible if i["category"] in ("boost", "upgrade")]
    rares = [i for i in eligible if i["rarity"] in ("rare", "legendary")]

    shop: list[dict] = []
    seen_ids: set[str] = set()

    def pick(pool: list[dict], n: int) -> None:
        available = [i for i in pool if i["id"] not in seen_ids]
        rng.shuffle(available)
        for item in available[:n]:
            shop.append(item)
            seen_ids.add(item["id"])

    pick(consumables, 2)
    pick(boosters, 2)
    pick(rares, 1)

    # Wild card — anything remaining
    remaining = [i for i in eligible if i["id"] not in seen_ids]
    pick(remaining, 1)

    return shop
