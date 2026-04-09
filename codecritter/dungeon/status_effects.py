"""Status effect system for dungeon combat."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StatusEffect:
    """A temporary effect applied to a combatant."""
    id: str                # e.g. "gil_lock", "memory_leak"
    name: str              # display name
    duration: int          # turns remaining (-1 = permanent until cleansed)
    effect_type: str       # "stun", "dot", "debuff", "shield", "delayed"
    value: int             # damage per turn, stat amount, shield HP, etc.
    source: str = "enemy"  # "enemy" or "player"

    def tick(self) -> bool:
        """Decrement duration. Returns True if the effect expired."""
        if self.duration == -1:
            return False
        self.duration -= 1
        return self.duration <= 0

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "duration": self.duration, "effect_type": self.effect_type,
            "value": self.value, "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> StatusEffect:
        return cls(**data)

    def display_tag(self) -> str:
        """Short display string for battle UI."""
        if self.effect_type == "stun":
            return "[STUN]"
        elif self.effect_type == "dot":
            return f"[DOT:{self.value}]"
        elif self.effect_type == "shield":
            return f"[SHIELD:{self.value}]"
        elif self.effect_type == "delayed":
            return f"[ASYNC:{self.duration}]"
        elif self.effect_type == "debuff":
            return f"[{self.name}]"
        return f"[{self.id}]"


def process_effects(effects: list[StatusEffect], hp: int) -> tuple[int, list[str]]:
    """Process all active effects. Returns (new_hp, log_messages).

    Callers should remove expired effects after calling this.
    """
    messages: list[str] = []
    for effect in effects:
        if effect.effect_type == "dot":
            hp = max(0, hp - effect.value)
            messages.append(f"{effect.name} deals {effect.value} damage!")
        # Stun is handled at action time, not here

    # Remove expired effects
    expired = []
    for effect in effects:
        if effect.tick():
            messages.append(f"{effect.name} wore off.")
            expired.append(effect)
    for e in expired:
        effects.remove(e)

    return hp, messages


def apply_shield_damage(effects: list[StatusEffect], damage: int) -> tuple[int, list[str]]:
    """Reduce damage through shield effects. Returns (remaining_damage, messages)."""
    messages: list[str] = []
    for effect in effects:
        if effect.effect_type == "shield" and damage > 0:
            absorbed = min(damage, effect.value)
            effect.value -= absorbed
            damage -= absorbed
            messages.append(f"{effect.name} absorbs {absorbed} damage!")
            if effect.value <= 0:
                messages.append(f"{effect.name} shatters!")
                effect.duration = 0  # mark for removal
    return damage, messages


def is_stunned(effects: list[StatusEffect]) -> bool:
    """Check if any active stun effect prevents action."""
    return any(e.effect_type == "stun" and e.duration > 0 for e in effects)


def resolve_delayed_damage(effects: list[StatusEffect], current_turn: int) -> tuple[int, list[str]]:
    """Resolve delayed damage effects that have reached turn 0.
    Returns (total_damage, messages).
    """
    damage = 0
    messages: list[str] = []
    for effect in effects:
        if effect.effect_type == "delayed" and effect.duration <= 0:
            damage += effect.value
            messages.append(f"The {effect.name} resolves! {effect.value} damage!")
    return damage, messages
