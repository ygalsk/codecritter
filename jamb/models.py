from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


TITLE_THRESHOLDS: list[tuple[int, str | dict[str, str]]] = [
    (1, "Hatchling"),
    (5, "Trail Blazer"),
    (
        10,
        {
            "debugging": "Bug Whisperer",
            "patience": "Zen Guardian",
            "chaos": "Chaos Agent",
            "wisdom": "Sage Keeper",
            "snark": "Roast Master",
        },
    ),
    (20, "Legendary Companion"),
    (30, "Ascended Champion"),
]

STAT_CAP = 255
XP_PER_LEVEL = 50

# Rarity-based progression caps — higher rarity = higher potential
RARITY_CAPS: dict[str, dict[str, int]] = {
    "Common": {"level": 20, "stat": 150},
    "Uncommon": {"level": 30, "stat": 180},
    "Rare": {"level": 50, "stat": 220},
    "Epic": {"level": 75, "stat": 245},
    "Legendary": {"level": 100, "stat": 255},
}

DEFAULT_RARITY_CAP = {"level": 100, "stat": 255}  # fallback if unknown

EVOLUTION_STAGES = [
    (1, "hatchling"),
    (10, "juvenile"),
    (20, "adult"),
]


@dataclass
class Stats:
    debugging: int = 61
    patience: int = 15
    chaos: int = 81
    wisdom: int = 49
    snark: int = 47

    def total(self) -> int:
        return self.debugging + self.patience + self.chaos + self.wisdom + self.snark

    def highest(self) -> str:
        d = self.as_dict()
        return max(d, key=d.get)  # type: ignore[arg-type]

    def add(self, stat_name: str, amount: int, rarity_cap: int = STAT_CAP) -> int:
        current = getattr(self, stat_name)
        cap = min(STAT_CAP, rarity_cap)
        new_val = min(current + amount, cap)
        setattr(self, stat_name, new_val)
        return new_val - current

    def as_dict(self) -> dict[str, int]:
        return {
            "debugging": self.debugging,
            "patience": self.patience,
            "chaos": self.chaos,
            "wisdom": self.wisdom,
            "snark": self.snark,
        }


@dataclass
class JambState:
    name: str = "Jamb"
    species: str = "Snail"
    rarity: str = "\u2605\u2605\u2605 RARE"
    level: int = 1
    xp: int = 0
    title: str = "Hatchling"
    stats: Stats = field(default_factory=Stats)
    total_sessions: int = 0
    created_at: Optional[str] = None
    last_session: Optional[str] = None
    stage: str = "hatchling"
    personality: str = (
        "Leaves glittering trails of nonsensical comments across your "
        "debug logs while somehow always pointing at the actual bug, "
        "though with a 50/50 chance of insisting it's a feature."
    )
    inventory: list[dict] = field(default_factory=list)
    equipment: dict[str, str] = field(default_factory=dict)
    gold: int = 0
    dungeon_highest_floor: int = 0
    inventory_capacity: int = 15
    # Native buddy bone sync
    native_rarity: Optional[str] = None  # e.g., "Uncommon", "Rare"
    native_stats: Optional[dict[str, int]] = None  # base stats from bones (0-100)
    bones_synced: bool = False
    # Buddy presentation layer (from claude-buddy fusion)
    eyes: Optional[str] = None          # eye style from bones (e.g., "°", "✦")
    hat: Optional[str] = None           # hat from bones (e.g., "crown", "wizard")
    shiny: bool = False                 # 1% shiny flag from bones
    reaction: Optional[str] = None      # current speech bubble text
    reaction_reason: Optional[str] = None  # why (error, pet, turn, buddy-comment)
    reaction_ts: Optional[float] = None # unix timestamp when reaction was set
    muted: bool = False                 # suppress reactions + buddy comments
    # Shared display state (TUI writes, statusline reads)
    current_quip: Optional[str] = None  # current speech text shown in TUI
    animation_frame: int = 0            # current animation frame index

    def rarity_cap(self) -> dict[str, int]:
        """Get level and stat caps based on native rarity."""
        if self.native_rarity:
            return RARITY_CAPS.get(self.native_rarity, DEFAULT_RARITY_CAP)
        return DEFAULT_RARITY_CAP

    def stat_cap(self) -> int:
        """Effective stat cap based on rarity."""
        return self.rarity_cap()["stat"]

    def clamp_to_caps(self) -> None:
        """Retroactively enforce rarity caps on stats and level."""
        cap = self.stat_cap()
        for stat_name in ("debugging", "patience", "chaos", "wisdom", "snark"):
            val = getattr(self.stats, stat_name)
            if val > cap:
                setattr(self.stats, stat_name, cap)
        self.level = min(self.level, self.level_cap())

    def level_cap(self) -> int:
        """Effective level cap based on rarity."""
        return self.rarity_cap()["level"]

    def xp_to_next_level(self) -> int:
        return self.level * XP_PER_LEVEL

    def add_xp(self, amount: int) -> str | None:
        """Add XP. Returns new stage name if evolved, None otherwise."""
        if self.level >= self.level_cap():
            return None
        old_stage = self.stage
        self.xp += amount
        while self.xp >= self.xp_to_next_level() and self.level < self.level_cap():
            self.xp -= self.xp_to_next_level()
            self.level += 1
        self._update_title()
        self._update_stage()
        if self.stage != old_stage:
            return self.stage
        return None

    def _update_stage(self) -> None:
        for threshold, stage in reversed(EVOLUTION_STAGES):
            if self.level >= threshold:
                self.stage = stage
                break

    def _update_title(self) -> None:
        for threshold, title in reversed(TITLE_THRESHOLDS):
            if self.level >= threshold:
                if isinstance(title, dict):
                    self.title = title.get(self.stats.highest(), "Trail Blazer")
                else:
                    self.title = title
                break

    def start_session(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if self.created_at is None:
            self.created_at = now
        self.last_session = now
        self.total_sessions += 1

    MAX_STACK = 10

    def inventory_slot_count(self) -> int:
        """Count how many slots are used. Stacked consumables = 1 slot."""
        return len(self.inventory)

    def inventory_full(self) -> bool:
        return self.inventory_slot_count() >= self.inventory_capacity

    def inventory_add(self, item: dict) -> bool:
        """Try to add an item to inventory. Returns True if added, False if full."""
        if item.get("type") == "consumable":
            for existing in self.inventory:
                if existing.get("id") == item.get("id") and existing.get("type") == "consumable":
                    count = existing.get("count", 1)
                    if count < self.MAX_STACK:
                        existing["count"] = count + 1
                        return True
                    break

        if self.inventory_full():
            return False

        new_item = dict(item)
        if new_item.get("type") == "consumable" and "count" not in new_item:
            new_item["count"] = 1
        self.inventory.append(new_item)
        return True

    def inventory_remove(self, idx: int, count: int = 1) -> dict | None:
        """Remove count items at index. Returns the item removed, or None."""
        if idx < 0 or idx >= len(self.inventory):
            return None
        item = self.inventory[idx]
        if item.get("type") == "consumable":
            current = item.get("count", 1)
            if current > count:
                item["count"] = current - count
                return dict(item)
            else:
                return self.inventory.pop(idx)
        else:
            return self.inventory.pop(idx)

    def sell_item(self, idx: int, count: int = 1) -> int:
        """Sell item(s) at index. Returns gold earned."""
        if idx < 0 or idx >= len(self.inventory):
            return 0
        item = self.inventory[idx]
        value = item.get("value", 0) // 2  # 50% sell price
        total = value * count
        self.inventory_remove(idx, count)
        self.gold += total
        return total

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "rarity": self.rarity,
            "level": self.level,
            "xp": self.xp,
            "title": self.title,
            "stats": self.stats.as_dict(),
            "total_sessions": self.total_sessions,
            "created_at": self.created_at,
            "last_session": self.last_session,
            "stage": self.stage,
            "personality": self.personality,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "gold": self.gold,
            "dungeon_highest_floor": self.dungeon_highest_floor,
            "inventory_capacity": self.inventory_capacity,
            "native_rarity": self.native_rarity,
            "native_stats": self.native_stats,
            "bones_synced": self.bones_synced,
            "eyes": self.eyes,
            "hat": self.hat,
            "shiny": self.shiny,
            "reaction": self.reaction,
            "reaction_reason": self.reaction_reason,
            "reaction_ts": self.reaction_ts,
            "muted": self.muted,
            "current_quip": self.current_quip,
            "animation_frame": self.animation_frame,
        }

    @classmethod
    def from_dict(cls, data: dict) -> JambState:
        state = cls()
        state.name = data.get("name", state.name)
        state.species = data.get("species", state.species)
        state.rarity = data.get("rarity", state.rarity)
        state.level = data.get("level", state.level)
        state.xp = data.get("xp", state.xp)
        state.title = data.get("title", state.title)
        state.total_sessions = data.get("total_sessions", state.total_sessions)
        state.created_at = data.get("created_at", state.created_at)
        state.last_session = data.get("last_session", state.last_session)
        state.personality = data.get("personality", state.personality)
        state.inventory = data.get("inventory", [])
        state.equipment = data.get("equipment", {})
        state.gold = data.get("gold", 0)
        state.dungeon_highest_floor = data.get("dungeon_highest_floor", 0)
        state.inventory_capacity = data.get("inventory_capacity", 15)
        state.native_rarity = data.get("native_rarity")
        state.native_stats = data.get("native_stats")
        state.bones_synced = data.get("bones_synced", False)
        state.eyes = data.get("eyes")
        state.hat = data.get("hat")
        state.shiny = data.get("shiny", False)
        state.reaction = data.get("reaction")
        state.reaction_reason = data.get("reaction_reason")
        state.reaction_ts = data.get("reaction_ts")
        state.muted = data.get("muted", False)
        state.current_quip = data.get("current_quip")
        state.animation_frame = data.get("animation_frame", 0)

        if "stats" in data:
            s = data["stats"]
            state.stats = Stats(
                debugging=s.get("debugging", 61),
                patience=s.get("patience", 15),
                chaos=s.get("chaos", 81),
                wisdom=s.get("wisdom", 49),
                snark=s.get("snark", 47),
            )

        # Recompute stage from level (handles old saves without stage field)
        state._update_stage()

        # Retroactively enforce rarity caps on existing saves
        state.clamp_to_caps()

        return state
