"""Combat engine and dungeon state management."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from .generator import Floor
from .items import CONSUMABLES, ITEMS_BY_ID, items_by_rarity
from .types import get_effectiveness, effectiveness_label
from .status_effects import StatusEffect, process_effects, apply_shield_damage, is_stunned


def _weapon_attack_bonus(weapon: dict) -> int:
    """Sum all attack-related bonuses from a weapon."""
    return (
        weapon.get("attack", 0)
        + weapon.get("debug_bonus", 0)
        + weapon.get("chaos_bonus", 0)
        + weapon.get("patience_bonus", 0)
    )


@dataclass
class CombatState:
    """Tracks state during a single combat encounter."""
    enemy: dict
    enemy_hp: int = 0
    enemy_max_hp: int = 0
    enemy_attack: int = 0
    enemy_defense: int = 0
    player_hp: int = 0
    player_max_hp: int = 0
    player_attack: int = 0
    player_defense: int = 0
    player_speed: int = 0
    crit_chance: int = 0
    dodge_chance: int = 0
    turn: int = 0
    attack_buff: int = 0
    buff_turns: int = 0
    defending: bool = False
    analyzed: bool = False  # wisdom special: next attack 2x
    weapon_type: str | None = None  # damage type of equipped weapon
    equipment: dict = field(default_factory=dict)  # current equipment ids
    log: list[str] = field(default_factory=list)
    finished: bool = False
    victory: bool = False
    # ── New fields ──────────────────────────────────────────────
    player_effects: list[StatusEffect] = field(default_factory=list)
    enemy_effects: list[StatusEffect] = field(default_factory=list)
    boss_phase: int = 1
    boss_max_phases: int = 1
    enemy_turn_count: int = 0
    pending_damage: list[tuple[int, int]] = field(default_factory=list)  # (resolve_turn, damage)
    # Stats reference for companion stat influences
    _stats: dict = field(default_factory=dict)

    @classmethod
    def from_stats(cls, enemy: dict, stats: dict, equipment: dict) -> CombatState:
        """Create combat state from Jamb's stats and equipped items."""
        debugging = stats.get("debugging", 0)
        patience = stats.get("patience", 0)
        chaos = stats.get("chaos", 0)
        wisdom = stats.get("wisdom", 0)
        snark = stats.get("snark", 0)

        base_attack = 5 + debugging // 10
        base_defense = 2 + patience // 15
        base_speed = 3 + chaos // 12

        # Equipment bonuses
        attack_bonus = 0
        defense_bonus = 0
        speed_bonus = 0

        weapon_type = None
        weapon = ITEMS_BY_ID.get(equipment.get("weapon", ""))
        if weapon:
            attack_bonus += _weapon_attack_bonus(weapon)
            weapon_type = weapon.get("damage_type")

        armor = ITEMS_BY_ID.get(equipment.get("armor", ""))
        if armor:
            defense_bonus += armor.get("defense", 0)
            defense_bonus += armor.get("wisdom_bonus", 0)

        accessory = ITEMS_BY_ID.get(equipment.get("accessory", ""))
        if accessory:
            attack_bonus += accessory.get("attack_bonus", 0)
            defense_bonus += accessory.get("defense_bonus", 0)
            speed_bonus += accessory.get("speed_bonus", 0)
            ab = accessory.get("all_bonus", 0)
            attack_bonus += ab
            defense_bonus += ab
            speed_bonus += ab

        max_hp = 50 + patience * 2
        boss_phases = enemy.get("boss_phases", 1)

        return cls(
            enemy=enemy,
            enemy_hp=enemy["hp"],
            enemy_max_hp=enemy["hp"],
            enemy_attack=enemy["attack"],
            enemy_defense=enemy["defense"],
            player_hp=max_hp,
            player_max_hp=max_hp,
            player_attack=base_attack + attack_bonus,
            player_defense=base_defense + defense_bonus,
            player_speed=base_speed + speed_bonus,
            crit_chance=min(50, chaos // 5),
            dodge_chance=min(25, snark // 10),
            weapon_type=weapon_type,
            equipment=dict(equipment),
            boss_phase=1,
            boss_max_phases=boss_phases,
            _stats=dict(stats),
        )

    def player_turn_attack(self) -> str:
        """Execute player attack."""
        if is_stunned(self.player_effects):
            msg = "Jamb is stunned and can't act!"
            self.log.append(msg)
            return msg

        self.defending = False
        attack_power = self.player_attack + self.attack_buff

        if self.analyzed:
            attack_power *= 2
            self.analyzed = False

        # Crit check
        is_crit = random.randint(1, 100) <= self.crit_chance
        if is_crit:
            attack_power = int(attack_power * 1.5)

        raw_damage = max(1, attack_power - self.enemy_defense + random.randint(-2, 3))

        # Type effectiveness
        enemy_type = self.enemy.get("type")
        multiplier = get_effectiveness(self.weapon_type, enemy_type)
        damage = max(1, int(raw_damage * multiplier))

        # Apply shield effects on enemy
        damage, shield_msgs = apply_shield_damage(self.enemy_effects, damage)
        for m in shield_msgs:
            self.log.append(m)

        self.enemy_hp = max(0, self.enemy_hp - damage)

        msg = f"Jamb attacks for {damage} damage!"
        if is_crit:
            msg = f"CRITICAL HIT! Jamb attacks for {damage} damage!"

        eff_label = effectiveness_label(multiplier)
        if eff_label:
            msg += f" {eff_label}"
        self.log.append(msg)

        self._check_enemy_defeated()
        self._check_boss_phase_transition()

        return msg

    def player_turn_defend(self) -> str:
        """Player defends this turn."""
        if is_stunned(self.player_effects):
            msg = "Jamb is stunned and can't act!"
            self.log.append(msg)
            return msg

        self.defending = True
        self.analyzed = False
        msg = "Jamb braces for impact! (Defense doubled this turn)"
        self.log.append(msg)
        return msg

    def player_turn_special(self, highest_stat: str) -> str:
        """Use special ability based on dominant stat."""
        if is_stunned(self.player_effects):
            msg = "Jamb is stunned and can't act!"
            self.log.append(msg)
            return msg

        self.defending = False
        self.analyzed = False

        # Special type matches the stat it's based on
        special_type = highest_stat
        enemy_type = self.enemy.get("type")
        multiplier = get_effectiveness(special_type, enemy_type)
        eff_label = effectiveness_label(multiplier)

        if highest_stat == "debugging":
            # Guaranteed hit, bonus damage
            raw_damage = self.player_attack + 5
            damage = max(1, int(raw_damage * multiplier))
            self.enemy_hp = max(0, self.enemy_hp - damage)
            msg = f"DEBUG MODE! Jamb traces the bug for {damage} guaranteed damage!"
        elif highest_stat == "patience":
            # Heal 25% HP (healing is not affected by type)
            heal = self.player_max_hp // 4
            self.player_hp = min(self.player_max_hp, self.player_hp + heal)
            msg = f"MEDITATE! Jamb retreats into shell and heals {heal} HP!"
            eff_label = None  # no type effectiveness on heals
        elif highest_stat == "chaos":
            # Random damage: could be huge or tiny
            raw_damage = random.randint(1, self.player_attack * 3)
            damage = max(1, int(raw_damage * multiplier))
            self.enemy_hp = max(0, self.enemy_hp - damage)
            msg = f"CHAOS STRIKE! Unpredictable blast for {damage} damage!"
        elif highest_stat == "wisdom":
            # Next attack does 2x
            self.analyzed = True
            msg = "ANALYZE! Jamb studies the enemy. Next attack deals 2x damage!"
            eff_label = None  # no direct damage
        elif highest_stat == "snark":
            # Taunt: enemy attack reduced, small damage
            raw_damage = max(1, self.player_attack // 2)
            damage = max(1, int(raw_damage * multiplier))
            self.enemy_hp = max(0, self.enemy_hp - damage)
            self.enemy_attack = max(1, self.enemy_attack - 2)
            msg = f"ROAST! Jamb trash-talks for {damage} damage! Enemy attack reduced!"
        else:
            raw_damage = self.player_attack
            damage = max(1, int(raw_damage * multiplier))
            self.enemy_hp = max(0, self.enemy_hp - damage)
            msg = f"Jamb attacks for {damage} damage!"

        if eff_label:
            msg += f" {eff_label}"
        self.log.append(msg)

        self._check_enemy_defeated()
        self._check_boss_phase_transition()

        return msg

    def player_turn_talk(self) -> tuple[bool, str]:
        """Attempt to talk the enemy out of fighting (SNARK ability).

        Returns (success, message).
        """
        snark = self._stats.get("snark", 0)
        success_chance = min(50, 20 + snark // 10)

        if random.randint(1, 100) <= success_chance:
            msg = f"Jamb roasts {self.enemy['name']} so hard it leaves in shame!"
            self.log.append(msg)
            self.finished = True
            self.victory = True
            return True, msg
        else:
            msg = f"Your roast falls flat. {self.enemy['name']} attacks in anger!"
            self.log.append(msg)
            # Free enemy attack
            self.enemy_turn()
            return False, msg

    def swap_weapon(self, new_weapon_id: str) -> str:
        """Swap equipped weapon mid-combat. Costs the player's turn."""
        self.defending = False
        self.analyzed = False

        weapon = ITEMS_BY_ID.get(new_weapon_id)
        if not weapon or weapon.get("type") != "weapon":
            msg = "Invalid weapon!"
            self.log.append(msg)
            return msg

        # Recalculate attack with new weapon
        old_weapon = ITEMS_BY_ID.get(self.equipment.get("weapon", ""))
        if old_weapon:
            self.player_attack -= _weapon_attack_bonus(old_weapon)

        self.player_attack += _weapon_attack_bonus(weapon)

        self.weapon_type = weapon.get("damage_type")
        self.equipment["weapon"] = new_weapon_id

        type_label = self.weapon_type.upper() if self.weapon_type else "???"
        msg = f"Swapped to {weapon['name']}! ({type_label}-type)"
        self.log.append(msg)
        return msg

    def player_use_item(self, item: dict, dungeon_run: DungeonRun | None = None) -> str:
        """Use a consumable item."""
        self.defending = False
        self.analyzed = False

        if item.get("heal"):
            heal = item["heal"]
            self.player_hp = min(self.player_max_hp, self.player_hp + heal)
            msg = f"Used {item['name']}! Healed {heal} HP."
        elif item.get("full_heal"):
            self.player_hp = self.player_max_hp
            msg = f"Used {item['name']}! Fully restored!"
        elif item.get("attack_buff"):
            self.attack_buff += item["attack_buff"]
            self.buff_turns = item.get("turns", 3)
            msg = f"Used {item['name']}! Attack +{item['attack_buff']} for {self.buff_turns} turns."
        elif item.get("save_hp") and dungeon_run:
            dungeon_run.saved_hp = self.player_hp
            msg = f"Used {item['name']}! Current HP ({self.player_hp}) stashed for later."
        elif item.get("revive") and dungeon_run:
            dungeon_run.has_revive = True
            msg = f"Used {item['name']}! Rollback point set — one free revive if defeated."
        else:
            msg = f"Used {item['name']}!"

        self.log.append(msg)
        return msg

    def player_restore_hp(self, dungeon_run: DungeonRun) -> str:
        """Restore HP from git stash. Costs a turn."""
        if dungeon_run.saved_hp is None:
            msg = "No stashed HP to restore!"
            self.log.append(msg)
            return msg

        old_hp = self.player_hp
        self.player_hp = min(self.player_max_hp, dungeon_run.saved_hp)
        dungeon_run.saved_hp = None
        msg = f"Restored stashed HP! ({old_hp} → {self.player_hp})"
        self.log.append(msg)
        return msg

    def enemy_turn(self) -> str:
        """Execute enemy turn."""
        self.enemy_turn_count += 1

        # Dodge check
        if random.randint(1, 100) <= self.dodge_chance:
            msg = f"Jamb dodges {self.enemy['name']}'s attack!"
            self.log.append(msg)
            return msg

        effective_defense = self.player_defense * (2 if self.defending else 1)
        damage = max(1, self.enemy_attack - effective_defense + random.randint(-1, 2))

        # Apply shield effects on player
        damage, shield_msgs = apply_shield_damage(self.player_effects, damage)
        for m in shield_msgs:
            self.log.append(m)

        self.player_hp = max(0, self.player_hp - damage)

        msg = f"{self.enemy['name']} attacks for {damage} damage!"
        if self.defending:
            msg += " (Blocked!)"
        self.log.append(msg)

        if self.player_hp <= 0:
            self.finished = True
            self.victory = False
            self.log.append("Jamb has been defeated!")

        return msg

    def apply_enemy_special(self) -> str | None:
        """Apply enemy special ability. Returns message or None."""
        special = self.enemy.get("special")
        if not special:
            return None

        msg = None

        # ── Original specials ───────────────────────────────
        if special == "grow":
            self.enemy_attack += 1
            msg = f"{self.enemy['name']} grows stronger! (ATK +1)"
        elif special == "double_attack":
            msg = self.enemy_turn()
            return f"Double attack! " + msg
        elif special == "lock" and random.random() < 0.3:
            self.player_effects.append(StatusEffect(
                id="lock", name="Deadlocked", duration=1,
                effect_type="stun", value=0,
            ))
            msg = "DEADLOCKED! Jamb can't move next turn!"
        elif special == "tangle":
            if self.player_attack > 3:
                self.player_attack -= 1
                msg = f"Tangled! Jamb's attack reduced! (ATK -{1})"
        elif special == "fortify":
            self.enemy_defense += 1
            msg = f"{self.enemy['name']} fortifies! (DEF +1)"
        elif special == "corrupt":
            effect = random.choice(["attack", "defense", "speed"])
            if effect == "attack" and self.player_attack > 3:
                self.player_attack -= 1
                msg = "Corrupted! Attack reduced!"
            elif effect == "defense" and self.player_defense > 1:
                self.player_defense -= 1
                msg = "Corrupted! Defense reduced!"
            else:
                msg = "Corruption fizzles..."

        # ── New biome specials ──────────────────────────────
        elif special == "dynamic_typing":
            from .types import TYPES
            old_type = self.enemy.get("type", "debugging")
            new_type = random.choice([t for t in TYPES if t != old_type])
            self.enemy["type"] = new_type
            msg = f"{self.enemy['name']} shifts type! Now {new_type.upper()}-type!"

        elif special == "gil_lock" and random.random() < 0.3:
            self.player_effects.append(StatusEffect(
                id="gil_lock", name="GIL Locked", duration=1,
                effect_type="stun", value=0,
            ))
            msg = "GIL LOCKED! Jamb can't act next turn!"

        elif special == "async_attack":
            damage = max(1, self.enemy_attack - self.player_defense // 2)
            resolve_turn = self.turn + 2
            self.pending_damage.append((resolve_turn, damage))
            msg = f"{self.enemy['name']} queues an async attack! (Resolves in 2 turns)"

        elif special == "callback_hell":
            # Handled at the screen level — sets a flag for random action
            self.player_effects.append(StatusEffect(
                id="callback_hell", name="Callback Hell", duration=2,
                effect_type="debuff", value=0,
            ))
            msg = "CALLBACK HELL! Jamb's actions may misfire!"

        elif special == "segfault_strike":
            # Massive hit every 3rd turn
            if self.enemy_turn_count % 3 == 0:
                damage = int(self.enemy_attack * 2.5)
                effective_defense = self.player_defense * (2 if self.defending else 1)
                actual = max(1, damage - effective_defense)
                self.player_hp = max(0, self.player_hp - actual)
                msg = f"SEGFAULT! {self.enemy['name']} crashes into Jamb for {actual} massive damage!"
                if self.player_hp <= 0:
                    self.finished = True
                    self.victory = False
                    self.log.append("Jamb has been defeated!")
            else:
                msg = f"{self.enemy['name']} glitches... building up to something."

        elif special == "memory_leak_drain":
            # Apply DoT if not already active
            has_dot = any(e.id == "memory_leak" for e in self.player_effects)
            if not has_dot:
                self.player_effects.append(StatusEffect(
                    id="memory_leak", name="Memory Leak", duration=4,
                    effect_type="dot", value=3,
                ))
                msg = "MEMORY LEAK! Jamb loses 3 HP per turn!"
            else:
                msg = "The memory leak continues to drain..."

        elif special == "borrow_checker":
            # Shield if not already active
            has_shield = any(e.id == "borrow_checker" for e in self.enemy_effects)
            if not has_shield:
                shield_hp = self.enemy_defense * 2
                self.enemy_effects.append(StatusEffect(
                    id="borrow_checker", name="Borrow Checker", duration=-1,
                    effect_type="shield", value=shield_hp,
                ))
                msg = f"BORROW CHECKER! A shield of {shield_hp} HP protects the enemy!"
            else:
                msg = "The borrow checker stands firm."

        elif special == "lifetime":
            self.enemy_attack += 2
            msg = f"{self.enemy['name']}'s lifetime grows! (ATK +2)"

        elif special == "goroutine_swarm":
            if self.enemy_hp <= self.enemy_max_hp // 2 and not hasattr(self, '_swarm_triggered'):
                self._swarm_triggered = True
                msg = f"{self.enemy['name']} splits into goroutines!"
                # The battle screen handles spawning sequential fights
            else:
                msg = f"{self.enemy['name']} spawns background goroutines..."

        elif special == "nil_panic":
            if random.random() < 0.05:
                damage = int(self.player_hp * 0.9)
                self.player_hp = max(1, self.player_hp - damage)
                msg = f"NIL PANIC! {self.enemy['name']} crashes Jamb for {damage} damage!"
                if self.player_hp <= 0:
                    self.finished = True
                    self.victory = False
                    self.log.append("Jamb has been defeated!")
            else:
                msg = f"{self.enemy['name']} twitches nervously..."

        if msg:
            self.log.append(msg)
        return msg

    def end_of_turn(self) -> list[str]:
        """Process end-of-turn effects. Returns log messages."""
        messages: list[str] = []
        self.turn += 1

        if self.buff_turns > 0:
            self.buff_turns -= 1
            if self.buff_turns <= 0:
                self.attack_buff = 0

        # Process player status effects
        self.player_hp, effect_msgs = process_effects(self.player_effects, self.player_hp)
        messages.extend(effect_msgs)

        # Process enemy status effects (remove expired shields etc.)
        self.enemy_hp, enemy_msgs = process_effects(self.enemy_effects, self.enemy_hp)
        messages.extend(enemy_msgs)

        # Resolve pending async damage
        resolved = []
        for resolve_turn, damage in self.pending_damage:
            if self.turn >= resolve_turn:
                actual = max(1, damage)
                self.player_hp = max(0, self.player_hp - actual)
                messages.append(f"The async attack resolves! {actual} damage!")
                resolved.append((resolve_turn, damage))
        for r in resolved:
            self.pending_damage.remove(r)

        # Check death from effects
        if self.player_hp <= 0:
            self.finished = True
            self.victory = False
            messages.append("Jamb has been defeated!")
        if self.enemy_hp <= 0:
            self.finished = True
            self.victory = True
            messages.append(f"{self.enemy['name']} is defeated!")

        # Equipment heal-per-turn effects are checked at the screen level
        self.defending = False

        for m in messages:
            self.log.append(m)

        return messages

    def _check_enemy_defeated(self) -> None:
        """Check if enemy HP reached 0."""
        if self.enemy_hp <= 0:
            self.finished = True
            self.victory = True
            self.log.append(f"{self.enemy['name']} is defeated!")

    def _check_boss_phase_transition(self) -> None:
        """Check for boss phase transitions at HP thresholds."""
        if self.boss_max_phases <= 1 or self.enemy_hp <= 0:
            return

        # Phase 2 at 50%, Phase 3 at 25%
        hp_pct = self.enemy_hp / self.enemy_max_hp
        target_phase = 1
        if hp_pct <= 0.25 and self.boss_max_phases >= 3:
            target_phase = 3
        elif hp_pct <= 0.5 and self.boss_max_phases >= 2:
            target_phase = 2

        if target_phase > self.boss_phase:
            self.boss_phase = target_phase
            # Heal 10% and boost stats
            heal = self.enemy_max_hp // 10
            self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
            self.enemy_attack += 2
            self.enemy_defense += 1
            self.finished = False  # Cancel any defeat from this hit
            self.victory = False
            msg = (
                f"*** {self.enemy['name']} enters Phase {self.boss_phase}! ***\n"
                f"   Heals {heal} HP! ATK +2, DEF +1!"
            )
            self.log.append(msg)

    def has_callback_hell(self) -> bool:
        """Check if callback hell debuff is active (for screen-level random action)."""
        return any(e.id == "callback_hell" for e in self.player_effects)

    def has_goroutine_split(self) -> bool:
        """Check if the goroutine swarm split was triggered."""
        return getattr(self, '_swarm_triggered', False)

    def calculate_rewards(self, talk_victory: bool = False) -> tuple[int, int, list[dict]]:
        """Return (xp, gold, loot_items) for victory."""
        if not self.victory:
            return 0, 0, []

        xp = self.enemy.get("xp", 10)
        gold = self.enemy.get("gold", 5)

        # Talk victories give partial rewards
        if talk_victory:
            xp = xp // 2
            gold = gold // 2
            return xp, gold, []

        loot = []
        for item_id, chance in self.enemy.get("loot", []):
            if random.random() < chance:
                item = ITEMS_BY_ID.get(item_id)
                if item:
                    loot.append(dict(item))

        return xp, gold, loot


@dataclass
class DungeonRun:
    """State for an active dungeon run."""
    floor: Floor
    hp: int
    max_hp: int
    gold_earned: int = 0
    xp_earned: int = 0
    items_found: list[dict] = field(default_factory=list)
    floors_cleared: int = 0
    alive: bool = True
    # ── New fields ──────────────────────────────────────────────
    biome: str = "generic"
    floor_modifier: dict | None = None  # active modifier for current floor
    banked_gold: int = 0
    banked_items: list[dict] = field(default_factory=list)
    enemies_defeated: int = 0
    saved_hp: int | None = None  # git stash saved HP
    has_revive: bool = False  # rollback scroll active
    action_counts: dict = field(default_factory=lambda: {
        "attack": 0, "defend": 0, "flee": 0, "item": 0, "special": 0,
    })
    last_death_enemy: str | None = None  # enemy id that killed us

    @classmethod
    def new_run(cls, stats: dict, equipment: dict, biome: str = "generic") -> DungeonRun:
        patience = stats.get("patience", 0)
        max_hp = 50 + patience * 2
        floor = Floor(number=1)
        floor.generate(biome=biome, stats=stats)
        return cls(floor=floor, hp=max_hp, max_hp=max_hp, biome=biome)

    def next_floor(self, stats: dict | None = None) -> None:
        self.floors_cleared += 1
        new_floor = Floor(number=self.floor.number + 1)
        # Pick a floor modifier (after floor 5)
        if self.floor.number + 1 >= 5:
            self.floor_modifier = self._pick_modifier()
        else:
            self.floor_modifier = None
        new_floor.generate(biome=self.biome, stats=stats, floor_modifier=self.floor_modifier)
        self.floor = new_floor

    def _pick_modifier(self) -> dict | None:
        """40% chance of no modifier; otherwise random."""
        if random.random() < 0.4:
            return None
        from . import data_loader
        modifiers = data_loader.load_floor_modifiers()
        if not modifiers:
            return None
        return random.choice(modifiers)

    def apply_trap(self, stats: dict, trap: dict | None = None) -> tuple[int, str]:
        """Apply trap damage. Returns (damage, message)."""
        wisdom = stats.get("wisdom", 0)
        patience = stats.get("patience", 0)

        if trap and "damage_range" in trap:
            lo, hi = trap["damage_range"]
            base_damage = random.randint(lo, hi)
            description = trap.get("description", "A trap springs!")
        else:
            base_damage = random.randint(5, 15)
            description = "Trap"

        # Wisdom reduces trap damage
        reduction = wisdom // 20
        # High patience further reduces
        if patience >= 80:
            reduction += 3

        damage = max(1, base_damage - reduction)
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.alive = False

        msg = f"{description} ({damage} damage!)"
        if reduction:
            msg += f" (Reduced by {reduction})"
        return damage, msg

    def rest(self, stats: dict | None = None) -> int:
        """Rest at a rest point. Returns HP healed."""
        # High patience heals 50% instead of 33%
        patience = (stats or {}).get("patience", 0)
        ratio = 2 if patience >= 80 else 3
        heal = min(self.max_hp // ratio, self.max_hp - self.hp)
        self.hp += heal
        return heal

    def bank_loot(self) -> tuple[int, int]:
        """Bank current un-banked loot at an extraction point.
        Returns (gold_banked, items_banked_count).
        """
        gold = self.gold_earned
        items = len(self.items_found)
        self.banked_gold += gold
        self.banked_items.extend(self.items_found)
        self.gold_earned = 0
        self.items_found = []
        return gold, items

    def generate_treasure(self) -> dict:
        """Generate random treasure loot."""
        roll = random.random()
        if roll < 0.4:
            pool = items_by_rarity("common")
        elif roll < 0.75:
            pool = items_by_rarity("uncommon")
        elif roll < 0.92:
            pool = items_by_rarity("rare")
        else:
            pool = items_by_rarity("legendary")

        if not pool:
            pool = items_by_rarity("common")

        item = random.choice(pool)
        gold = random.randint(5, 20)
        self.gold_earned += gold
        return {"item": dict(item), "gold": gold}
