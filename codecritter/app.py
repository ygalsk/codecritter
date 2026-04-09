from __future__ import annotations

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Label

from . import persistence
from .models import CodecritterState
from .screens.main_screen import MainScreen
from .screens.evolution_screen import EvolutionScreen
from .screens.dungeon_screen import DungeonScreen
from .screens.battle_screen import BattleScreen
from .screens.loot_screen import LootScreen
from .screens.inventory_screen import InventoryScreen
from .screens.shop_screen import ShopScreen
from .screens.extraction_screen import ExtractionScreen
from .screens.shop_dungeon_screen import DungeonShopScreen
from .screens.fork_screen import ForkScreen
from .dungeon.engine import CombatState, DungeonRun
from .dungeon.detection import detect_language
from .dungeon import history as dungeon_history
from .widgets.ascii_art import SnailArt
from .widgets.speech_bubble import SpeechBubble

CODECRITTER_THEME = Theme(
    name="codecritter",
    primary="#BB9AF7",
    secondary="#7AA2F7",
    accent="#FF9E64",
    background="#1A1B26",
    surface="#24283B",
    panel="#414868",
    foreground="#a9b1d6",
    warning="#E0AF68",
    error="#F7768E",
    success="#9ECE6A",
    dark=True,
)


class CodecritterApp(App):
    CSS_PATH = "codecritter.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.register_theme(CODECRITTER_THEME)
        self.theme = "codecritter"
        self.state: CodecritterState = persistence.load()
        self.dungeon_run: DungeonRun | None = None
        self._last_known_mtime: float = 0.0

    def on_mount(self) -> None:
        self._save_and_track()
        self.push_screen(MainScreen())
        # Start animation timer
        self.set_interval(2.0, self._animate_snail)
        # File watcher: detect external changes to save.json (from hooks)
        self._last_known_mtime = self._get_save_mtime()
        self.set_interval(2.5, self._check_external_changes)

    def _get_save_mtime(self) -> float:
        try:
            return persistence.SAVE_FILE.stat().st_mtime
        except OSError:
            return 0.0

    def _save_and_track(self) -> None:
        """Save state and update mtime tracker so file watcher ignores own writes."""
        persistence.save(self.state)
        self._last_known_mtime = self._get_save_mtime()

    def _check_external_changes(self) -> None:
        """Poll save.json for external modifications (from hooks)."""
        current_mtime = self._get_save_mtime()
        if current_mtime > self._last_known_mtime:
            self._last_known_mtime = current_mtime
            self._reload_from_disk()

    def _reload_from_disk(self) -> None:
        """Reload state from save.json without starting a new session."""
        try:
            data = json.loads(persistence.SAVE_FILE.read_text())
            new_state = CodecritterState.from_dict(data.get("codecritter", data.get("jamb", {})))
        except (json.JSONDecodeError, KeyError, OSError):
            return

        # Preserve session-specific state
        new_state.total_sessions = self.state.total_sessions
        self.state = new_state

        # Refresh the visible screen (widget posts Changed message → on_speech_bubble_changed)
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.refresh_state()

    def on_speech_bubble_changed(self, event: SpeechBubble.Changed) -> None:
        """Immediately sync speech text to save.json whenever widget changes."""
        self.state.current_quip = event.text
        self._save_and_track()

    def show_main(self) -> None:
        while len(self.screen_stack) > 2:
            self.pop_screen()
        main = self.screen
        if isinstance(main, MainScreen):
            main.refresh_state()
        else:
            self.push_screen(MainScreen())

    def show_dungeon(self) -> None:
        if not self.dungeon_run:
            biome = detect_language()
            self.dungeon_run = DungeonRun.new_run(
                self.state.stats.as_dict(),
                self.state.equipment,
                biome=biome,
            )
        self._push_over_main(DungeonScreen())

    def show_extraction(self) -> None:
        self._push_over_main(ExtractionScreen())

    def show_dungeon_shop(self) -> None:
        self._push_over_main(DungeonShopScreen())

    def show_fork(self, fork_options: list) -> None:
        self._push_over_main(ForkScreen(fork_options=fork_options))

    def show_inventory(self) -> None:
        self._push_over_main(InventoryScreen())

    def show_shop(self) -> None:
        self._push_over_main(ShopScreen())

    def show_loot(self, loot: dict) -> None:
        # Add items to inventory (with stacking and capacity check)
        dropped = []
        if "item" in loot and loot["item"]:
            if not self.state.inventory_add(loot["item"]):
                dropped.append(loot["item"])
        for item in loot.get("items", []):
            if not self.state.inventory_add(item):
                dropped.append(item)
        # Pass dropped info to loot screen instead of using a toast
        loot["_dropped"] = dropped
        self.state.gold += loot.get("gold", 0)
        if self.dungeon_run:
            self.dungeon_run.gold_earned += loot.get("gold", 0)
        self._save_and_track()
        self._push_over_main(LootScreen(loot))

    def start_combat(self, enemy: dict) -> None:
        combat = CombatState.from_stats(
            enemy, self.state.stats.as_dict(), self.state.equipment,
        )
        if self.dungeon_run:
            combat.player_hp = self.dungeon_run.hp
            combat.player_max_hp = self.dungeon_run.max_hp

        # Add taunts/hints from history
        hist = self._ensure_dungeon_history()
        enemy_id = enemy.get("id", "")
        enemy_type = enemy.get("type", "")
        for taunt in dungeon_history.get_taunts(hist, enemy_id):
            combat.log.append(taunt)
        for hint in dungeon_history.get_hints(hist, enemy_id, enemy_type):
            combat.log.append(hint)

        # High DEBUGGING: reveal enemy stats
        debugging = self.state.stats.debugging
        if debugging >= 80:
            combat.log.append(
                f"[DEBUG] {enemy.get('name', '?')}: "
                f"ATK={enemy.get('attack', '?')} DEF={enemy.get('defense', '?')} "
                f"SPD={enemy.get('speed', '?')} Type={enemy_type.upper()}"
            )

        self._push_over_main(BattleScreen(combat))

    def combat_victory(self, xp: int, gold: int, loot: list[dict]) -> None:
        run = self.dungeon_run
        if run:
            room = run.floor.current_room()
            room.cleared = True
            run.xp_earned += xp
            run.gold_earned += gold
            run.enemies_defeated += 1

        self.state.gold += gold
        self.state.add_xp(xp)
        self._save_and_track()

        if loot:
            # Loot screen shows the full breakdown — no toast needed
            self.show_loot({"items": loot, "gold": gold, "xp": xp})
        else:
            self.notify(
                f"+{xp} XP  +{gold} Gold",
                title="Victory!",
                timeout=3,
            )
            self.show_dungeon()

    def dungeon_death(self) -> None:
        run = self.dungeon_run
        if not run:
            self.show_main()
            return

        # Check for rollback scroll revive
        if run.has_revive:
            run.has_revive = False
            run.hp = max(1, run.max_hp // 4)
            run.alive = True
            self.notify(
                "Rollback Scroll activated! Revived at 25% HP.",
                title="ROLLBACK!",
                timeout=4,
            )
            self.show_dungeon()
            return

        # Record death in history
        hist = self._ensure_dungeon_history()
        enemy_room = run.floor.current_room()
        enemy_id = enemy_room.enemy.get("id", "unknown") if enemy_room.enemy else "unknown"
        enemy_name = enemy_room.enemy.get("name", "Unknown") if enemy_room.enemy else "Unknown"
        run.last_death_enemy = enemy_id
        dungeon_history.record_death(hist, enemy_id, enemy_name, run.floor.number, run.biome)
        dungeon_history.record_run(
            hist, run.floors_cleared, run.biome, enemy_id,
            run.gold_earned, run.enemies_defeated, False,
        )
        dungeon_history.merge_action_counts(hist, run.action_counts)

        # Keep banked loot, lose un-banked items/gold
        kept_xp = run.xp_earned // 2
        self.state.add_xp(kept_xp)
        self.state.gold += run.banked_gold  # banked gold is safe
        # banked items stay in inventory (already added during extraction)

        if run.floor.number > self.state.dungeon_highest_floor:
            self.state.dungeon_highest_floor = run.floor.number

        # Check unlocks
        new_unlocks = dungeon_history.check_unlocks(hist, run.floors_cleared, None, run.biome)

        self.dungeon_run = None
        self._save_and_track()

        msg = f"Jamb was defeated! Kept {kept_xp} XP."
        if run.banked_gold > 0:
            msg += f" Banked {run.banked_gold} gold saved."
        self.notify(msg, title="Dungeon Over", severity="warning", timeout=4)

        if new_unlocks:
            self.notify(
                f"New unlocks: {', '.join(new_unlocks)}",
                title="Achievement!",
                timeout=4,
            )
        self.show_main()

    def end_dungeon(self, fled: bool = False) -> None:
        run = self.dungeon_run
        if run:
            self.state.add_xp(run.xp_earned)
            self.state.gold += run.banked_gold
            if run.floor.number > self.state.dungeon_highest_floor:
                self.state.dungeon_highest_floor = run.floor.number

            # Record run history
            hist = self._ensure_dungeon_history()
            dungeon_history.record_run(
                hist, run.floors_cleared, run.biome, None,
                run.gold_earned + run.banked_gold, run.enemies_defeated, not fled,
            )
            dungeon_history.merge_action_counts(hist, run.action_counts)

            # Check unlocks
            new_unlocks = dungeon_history.check_unlocks(hist, run.floors_cleared, None, run.biome)
            if new_unlocks:
                self.notify(
                    f"New unlocks: {', '.join(new_unlocks)}",
                    title="Achievement!",
                    timeout=4,
                )

        self.dungeon_run = None
        self._save_and_track()
        if fled:
            self.notify("Fled the dungeon! XP and loot kept.", timeout=3)
        self.show_main()

    def _ensure_dungeon_history(self) -> dict:
        """Get or initialize dungeon_history on state."""
        if not hasattr(self.state, 'dungeon_history') or self.state.dungeon_history is None:
            self.state.dungeon_history = dungeon_history.empty_history()
        return self.state.dungeon_history

    def _push_over_main(self, screen) -> None:
        """Push a screen, popping any non-main screen first."""
        while len(self.screen_stack) > 2:
            self.pop_screen()
        self.push_screen(screen)

    def _animate_snail(self) -> None:
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.animate_snail()
            # Update frame in memory — persisted on next event-driven save
            try:
                snail = screen.query_one("#snail-art", SnailArt)
                self.state.animation_frame = snail._frame_idx
            except Exception:
                pass

    def save_and_quit(self) -> None:
        self._save_and_track()
        self.exit()
