"""Turn-based battle screen for dungeon combat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label, RichLog

from ..constants import C, TYPE_COLORS, render_bar
from ..dungeon.engine import CombatState
from ..dungeon.items import ITEMS_BY_ID
from ..dungeon.types import get_effectiveness, effectiveness_label

if TYPE_CHECKING:
    from ..app import CodecritterApp


class BattleScreen(Screen):
    """Turn-based RPG combat."""

    BINDINGS = [
        ("a", "attack", "Attack"),
        ("d", "defend", "Defend"),
        ("s", "special", "Special"),
        ("i", "use_item", "Item"),
        ("w", "swap_weapon", "Swap"),
        ("t", "talk", "Talk"),
        ("f", "flee", "Flee"),
    ]

    def __init__(self, combat: CombatState, **kwargs) -> None:
        super().__init__(**kwargs)
        self._combat = combat
        self._awaiting_continue = False
        self._swap_selecting = False
        self._swap_weapons: list[dict] = []
        self._item_selecting = False
        self._item_list: list[tuple[int, dict]] = []
        self._fled = False

    def compose(self) -> ComposeResult:
        with Vertical(id="battle-box") as box:
            box.border_title = " BATTLE "

            with Vertical(id="enemy-panel") as ep:
                ep.border_title = " Enemy "
                yield Label("", id="enemy-art")
                yield Label("", id="enemy-info")

            with Vertical(id="player-panel") as pp:
                pp.border_title = " Jamb "
                yield Label("", id="player-info")

            with Vertical(id="battle-log-panel") as lp:
                lp.border_title = " Battle Log "
                yield RichLog(id="battle-log", markup=True, max_lines=50)

            with Vertical(id="action-bar"):
                yield Label("", id="action-prompt")

        yield Footer()

    def on_mount(self) -> None:
        # Write any pre-combat log entries (taunts, hints, debug info)
        if self._combat.log:
            self._write_log(self._combat.log[:])
        self._refresh()

    def _refresh(self) -> None:
        c = self._combat

        art = c.enemy.get("art", "  ???")
        self.query_one("#enemy-art", Label).update(f"[{C.ERROR}]{art}[/]")

        enemy_hp_bar = render_bar(c.enemy_hp, c.enemy_max_hp)
        enemy_type = c.enemy.get("type", "???")
        type_color = TYPE_COLORS.get(enemy_type, "#888888")
        phase_label = ""
        if c.boss_max_phases > 1:
            phase_label = f"  [bold #FF9E64]Phase {c.boss_phase}/{c.boss_max_phases}[/]"
        enemy_effects_str = " ".join(e.display_tag() for e in c.enemy_effects)
        if enemy_effects_str:
            enemy_effects_str = f"  [{C.PRIMARY}]{enemy_effects_str}[/]"
        self.query_one("#enemy-info", Label).update(
            f"  [bold {C.ERROR}]{c.enemy['name']}[/]  "
            f"[{type_color}][{enemy_type.upper()}][/]  "
            f"[{C.ERROR}]{enemy_hp_bar}[/] {c.enemy_hp}/{c.enemy_max_hp} HP  "
            f"ATK:{c.enemy_attack} DEF:{c.enemy_defense}"
            f"{phase_label}{enemy_effects_str}"
        )

        player_hp_bar = render_bar(c.player_hp, c.player_max_hp)
        buffs = ""
        if c.attack_buff > 0:
            buffs += f" [{C.WARNING}]ATK+{c.attack_buff}({c.buff_turns}t)[/]"
        if c.analyzed:
            buffs += f" [{C.PRIMARY}]ANALYZED(2x)[/]"

        weapon_info = ""
        if c.weapon_type:
            wt_color = TYPE_COLORS.get(c.weapon_type, "#888888")
            weapon_name = ""
            weapon_data = ITEMS_BY_ID.get(c.equipment.get("weapon", ""))
            if weapon_data:
                weapon_name = weapon_data["name"] + " "
            weapon_info = f"  [{wt_color}]{weapon_name}[{c.weapon_type.upper()}][/]"

        player_effects_str = " ".join(e.display_tag() for e in c.player_effects)
        if player_effects_str:
            player_effects_str = f"  [{C.ERROR}]{player_effects_str}[/]"

        self.query_one("#player-info", Label).update(
            f"  [bold {C.SUCCESS}]Jamb[/]  "
            f"[{C.SUCCESS}]{player_hp_bar}[/] {c.player_hp}/{c.player_max_hp} HP  "
            f"ATK:{c.player_attack + c.attack_buff} DEF:{c.player_defense} SPD:{c.player_speed}"
            f"{buffs}{weapon_info}{player_effects_str}"
        )

        if self._awaiting_continue:
            if c.victory:
                self.query_one("#action-prompt", Label).update(
                    f"  [{C.SUCCESS} bold]VICTORY![/] Press any key to continue."
                )
            else:
                self.query_one("#action-prompt", Label).update(
                    f"  [{C.ERROR} bold]DEFEATED![/] Press any key to continue."
                )
        elif self._item_selecting:
            lines = ["  [bold]Use item:[/] (ESC to cancel)"]
            for i, (_, item) in enumerate(self._item_list):
                count = item.get("count", 1)
                count_text = f" x{count}" if count > 1 else ""
                effect = ""
                if item.get("heal"):
                    effect = f"HP+{item['heal']}"
                elif item.get("full_heal"):
                    effect = "FULL HEAL"
                elif item.get("attack_buff"):
                    effect = f"ATK+{item['attack_buff']} {item.get('turns', 3)}t"
                elif item.get("save_hp"):
                    effect = "SAVE STATE"
                elif item.get("revive"):
                    effect = "REVIVE"
                lines.append(
                    f"  [bold {C.ACCENT}]{i + 1}[/] {item['name']}{count_text} "
                    f"[{C.MUTED}]({effect})[/]"
                )
            self.query_one("#action-prompt", Label).update("\n".join(lines))
        elif self._swap_selecting:
            lines = ["  [bold]Swap weapon:[/] (ESC to cancel)"]
            for i, w in enumerate(self._swap_weapons):
                dt = w.get("damage_type", "???")
                color = TYPE_COLORS.get(dt, "#888888")
                lines.append(
                    f"  [bold {C.ACCENT}]{i + 1}[/] {w['name']} "
                    f"(ATK:{w.get('attack', 0)}) [{color}][{dt.upper()}][/]"
                )
            self.query_one("#action-prompt", Label).update("\n".join(lines))
        else:
            app: CodecritterApp = self.app  # type: ignore[assignment]
            highest = app.state.stats.highest()
            special_names = {
                "debugging": "Debug", "patience": "Meditate",
                "chaos": "Chaos Strike", "wisdom": "Analyze", "snark": "Roast",
            }
            special_name = special_names.get(highest, "Special")
            # Show Talk action if SNARK >= 80 and not a boss
            talk_label = ""
            snark = app.state.stats.snark
            is_boss = c.enemy.get("boss_phases", 1) > 1 or c.boss_max_phases > 1
            if snark >= 80 and not is_boss:
                talk_label = f"  [bold {C.ACCENT}]T[/]alk"

            # Show Restore if git stash HP is saved
            restore_label = ""
            run = app.dungeon_run
            if run and run.saved_hp is not None:
                restore_label = f"  [bold {C.ACCENT}]R[/]estore"

            self.query_one("#action-prompt", Label).update(
                f"  [bold {C.ACCENT}]A[/]ttack  [bold {C.ACCENT}]D[/]efend  "
                f"[bold {C.ACCENT}]S[/]pecial({special_name})  [bold {C.ACCENT}]I[/]tem  "
                f"[bold {C.ACCENT}]W[/]eapon{talk_label}{restore_label}  [bold {C.ACCENT}]F[/]lee"
            )

    def _write_log(self, entries: list[str]) -> None:
        log = self.query_one("#battle-log", RichLog)
        for entry in entries:
            log.write(f"  > {entry}")

    def _track_action(self, action: str) -> None:
        """Track player action for playstyle history."""
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if run and action in run.action_counts:
            run.action_counts[action] += 1

    def _do_enemy_turn(self) -> None:
        c = self._combat
        if c.finished:
            return
        log_before = len(c.log)
        c.apply_enemy_special()
        if not c.finished:
            c.enemy_turn()
        c.end_of_turn()
        new_entries = c.log[log_before:]
        if new_entries:
            self._write_log(new_entries)
        if c.finished:
            self._awaiting_continue = True
        self._refresh()

    def _end_battle(self) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        c = self._combat
        if self._fled:
            # Fled — just return to dungeon, HP preserved
            if app.dungeon_run:
                app.dungeon_run.hp = c.player_hp
            app.show_dungeon()
        elif c.victory:
            xp, gold, loot = c.calculate_rewards()
            # Sync HP back to dungeon run
            if app.dungeon_run:
                app.dungeon_run.hp = c.player_hp
            app.combat_victory(xp, gold, loot)
        else:
            app.dungeon_death()

    def on_key(self, event) -> None:
        if self._awaiting_continue:
            self._end_battle()
            return

        if self._item_selecting:
            if event.key == "escape":
                self._item_selecting = False
                self._refresh()
                return
            if event.character and event.character.isdigit():
                idx = int(event.character) - 1
                if 0 <= idx < len(self._item_list):
                    inv_idx, item = self._item_list[idx]
                    app: CodecritterApp = self.app  # type: ignore[assignment]
                    log_before = len(self._combat.log)
                    self._combat.player_use_item(item, dungeon_run=app.dungeon_run)
                    app.state.inventory_remove(inv_idx, 1)
                    self._track_action("item")
                    new_entries = self._combat.log[log_before:]
                    if new_entries:
                        self._write_log(new_entries)
                    self._item_selecting = False
                    self._do_enemy_turn()
            return

        if self._swap_selecting:
            if event.key == "escape":
                self._swap_selecting = False
                self._refresh()
                return
            if event.character and event.character.isdigit():
                idx = int(event.character) - 1
                if 0 <= idx < len(self._swap_weapons):
                    weapon = self._swap_weapons[idx]
                    app: CodecritterApp = self.app  # type: ignore[assignment]
                    old_weapon_id = app.state.equipment.get("weapon")
                    app.state.equipment["weapon"] = weapon["id"]
                    for i, item in enumerate(app.state.inventory):
                        if item.get("id") == weapon["id"]:
                            app.state.inventory.pop(i)
                            break
                    if old_weapon_id:
                        old_weapon = ITEMS_BY_ID.get(old_weapon_id)
                        if old_weapon:
                            app.state.inventory_add(dict(old_weapon))
                    self._combat.swap_weapon(weapon["id"])
                    self._write_log([f"Swapped to {weapon['name']}!"])
                    self._swap_selecting = False
                    self._do_enemy_turn()
            return

    def action_attack(self) -> None:
        if self._awaiting_continue or self._item_selecting:
            return
        c = self._combat
        self._track_action("attack")
        log_before = len(c.log)
        c.player_turn_attack()
        new_entries = c.log[log_before:]
        if new_entries:
            self._write_log(new_entries)
        if not c.finished:
            self._do_enemy_turn()
        else:
            self._awaiting_continue = True
            self._refresh()

    def action_defend(self) -> None:
        if self._awaiting_continue or self._item_selecting:
            return
        c = self._combat
        self._track_action("defend")
        log_before = len(c.log)
        c.player_turn_defend()
        new_entries = c.log[log_before:]
        if new_entries:
            self._write_log(new_entries)
        self._do_enemy_turn()

    def action_special(self) -> None:
        if self._awaiting_continue or self._item_selecting:
            return
        app: CodecritterApp = self.app  # type: ignore[assignment]
        c = self._combat
        self._track_action("special")
        highest = app.state.stats.highest()
        log_before = len(c.log)
        c.player_turn_special(highest)
        new_entries = c.log[log_before:]
        if new_entries:
            self._write_log(new_entries)
        if not c.finished:
            self._do_enemy_turn()
        else:
            self._awaiting_continue = True
            self._refresh()

    def action_talk(self) -> None:
        if self._awaiting_continue or self._item_selecting or self._swap_selecting:
            return
        app: CodecritterApp = self.app  # type: ignore[assignment]
        c = self._combat

        # Only available with high SNARK and non-boss
        snark = app.state.stats.snark
        is_boss = c.enemy.get("boss_phases", 1) > 1 or c.boss_max_phases > 1
        if snark < 80 or is_boss:
            self._write_log(["Can't talk your way out of this one!"])
            return

        log_before = len(c.log)
        success, msg = c.player_turn_talk()
        new_entries = c.log[log_before:]
        if new_entries:
            self._write_log(new_entries)

        if c.finished:
            self._awaiting_continue = True
            self._refresh()
        else:
            # Talk failed, enemy already attacked in player_turn_talk
            c.end_of_turn()
            self._refresh()

    def action_use_item(self) -> None:
        if self._awaiting_continue or self._swap_selecting or self._item_selecting:
            return
        app: CodecritterApp = self.app  # type: ignore[assignment]
        consumables = [
            (i, item) for i, item in enumerate(app.state.inventory)
            if item.get("type") == "consumable"
        ]
        if not consumables:
            self._write_log(["No consumables in inventory!"])
            return
        self._item_list = consumables[:9]
        self._item_selecting = True
        self._refresh()

    def action_swap_weapon(self) -> None:
        if self._awaiting_continue or self._swap_selecting or self._item_selecting:
            return
        app: CodecritterApp = self.app  # type: ignore[assignment]
        weapons = [
            item for item in app.state.inventory
            if item.get("type") == "weapon"
        ]
        if not weapons:
            self._write_log(["No other weapons in inventory!"])
            return
        self._swap_weapons = weapons[:9]
        self._swap_selecting = True
        self._refresh()

    def action_flee(self) -> None:
        if self._awaiting_continue or self._item_selecting:
            return
        import random
        c = self._combat
        self._track_action("flee")
        flee_chance = 40 + c.player_speed * 2
        if random.randint(1, 100) <= flee_chance:
            self._write_log(["Jamb fled successfully!"])
            c.finished = True
            c.victory = False
            self._fled = True
            self._awaiting_continue = True
            self._refresh()
        else:
            self._write_log(["Failed to flee!"])
            self._do_enemy_turn()
