from __future__ import annotations

import json
import random
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Label

from . import persistence
from .models import JambState
from .screens.main_screen import MainScreen
from .screens.evolution_screen import EvolutionScreen
from .screens.dungeon_screen import DungeonScreen
from .screens.battle_screen import BattleScreen
from .screens.loot_screen import LootScreen
from .screens.inventory_screen import InventoryScreen
from .screens.shop_screen import ShopScreen
from .dungeon.engine import CombatState, DungeonRun
from .widgets.ascii_art import SnailArt
from .widgets.speech_bubble import SpeechBubble

JAMB_THEME = Theme(
    name="jamb",
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


class JambApp(App):
    CSS_PATH = "jamb.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.register_theme(JAMB_THEME)
        self.theme = "jamb"
        self.state: JambState = persistence.load()
        self.dungeon_run: DungeonRun | None = None
        self._last_known_mtime: float = 0.0

    def on_mount(self) -> None:
        self._save_and_track()
        self.push_screen(MainScreen())
        # Start animation timers
        self.set_interval(2.0, self._animate_snail)
        self._schedule_speech_rotation()
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
            new_state = JambState.from_dict(data.get("jamb", {}))
        except (json.JSONDecodeError, KeyError, OSError):
            return

        # Detect meaningful changes
        old_xp = self.state.xp + self.state.level * 1000
        new_xp = new_state.xp + new_state.level * 1000
        gained_xp = new_xp > old_xp

        # Preserve session-specific state
        new_state.total_sessions = self.state.total_sessions
        self.state = new_state

        # Refresh the visible screen
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.refresh_state()

        if gained_xp:
            self.notify("Jamb earned a reward!", timeout=2)

    def _schedule_speech_rotation(self) -> None:
        self.set_timer(random.uniform(15, 45), self._rotate_speech_and_reschedule)

    def _rotate_speech_and_reschedule(self) -> None:
        self._rotate_speech()
        self._schedule_speech_rotation()

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
            self.dungeon_run = DungeonRun.new_run(
                self.state.stats.as_dict(),
                self.state.equipment,
            )
        self._push_over_main(DungeonScreen())

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
        self._push_over_main(BattleScreen(combat))

    def combat_victory(self, xp: int, gold: int, loot: list[dict]) -> None:
        run = self.dungeon_run
        if run:
            room = run.floor.current_room()
            room.cleared = True
            run.xp_earned += xp
            run.gold_earned += gold

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
        kept_xp = 0
        if run:
            kept_xp = run.xp_earned // 2
            self.state.add_xp(kept_xp)
            if run.floor.number > self.state.dungeon_highest_floor:
                self.state.dungeon_highest_floor = run.floor.number
        self.dungeon_run = None
        self._save_and_track()
        self.notify(
            f"Jamb was defeated! Kept {kept_xp} XP.",
            title="Dungeon Over",
            severity="warning",
            timeout=4,
        )
        self.show_main()

    def end_dungeon(self, fled: bool = False) -> None:
        run = self.dungeon_run
        if run:
            self.state.add_xp(run.xp_earned)
            if run.floor.number > self.state.dungeon_highest_floor:
                self.state.dungeon_highest_floor = run.floor.number
        self.dungeon_run = None
        self._save_and_track()
        if fled:
            self.notify("Fled the dungeon! XP and loot kept.", timeout=3)
        self.show_main()

    def _push_over_main(self, screen) -> None:
        """Push a screen, popping any non-main screen first."""
        while len(self.screen_stack) > 2:
            self.pop_screen()
        self.push_screen(screen)

    def _animate_snail(self) -> None:
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.animate_snail()
            # Sync frame index to state for statusline
            try:
                snail = screen.query_one("#snail-art", SnailArt)
                self.state.animation_frame = snail._frame_idx
            except Exception:
                pass

    def _rotate_speech(self) -> None:
        screen = self.screen
        if isinstance(screen, MainScreen):
            screen.rotate_speech()
            # Sync current quip to state for statusline
            try:
                speech = screen.query_one("#speech-bubble", SpeechBubble)
                text = str(speech.render()).strip().strip('"')
                self.state.current_quip = text
                self._save_and_track()
            except Exception:
                pass

    def save_and_quit(self) -> None:
        self._save_and_track()
        self.exit()
