"""Fork room screen — choose between two mysterious paths."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from ..constants import C
from ..dungeon.generator import ENEMY, REST, TRAP, TREASURE

if TYPE_CHECKING:
    from ..app import CodecritterApp


class ForkScreen(Screen):
    """Present a blind choice between two paths."""

    BINDINGS = [
        ("1", "choose_1", "Path 1"),
        ("2", "choose_2", "Path 2"),
        ("escape", "back", "Back"),
    ]

    def __init__(self, fork_options: list, **kwargs) -> None:
        super().__init__(**kwargs)
        self._options = fork_options  # [(description, hidden_type), ...]

    def compose(self) -> ComposeResult:
        with Vertical(id="fork-box") as box:
            box.border_title = " FORK IN THE PATH "

            yield Label(f"  [{C.SECONDARY} bold]═══  THE PATH SPLITS  ═══[/]", classes="mt1")
            yield Label("")
            yield Label(f"  [{C.MUTED}]Two passages branch before you.[/]")
            yield Label(f"  [{C.MUTED}]Choose wisely — you can't go back.[/]")
            yield Label("")

            for i, (desc, _) in enumerate(self._options, 1):
                yield Label(f"  [{C.ACCENT} bold][{i}][/] {desc}")
                yield Label("")

        yield Footer()

    def _resolve(self, index: int) -> None:
        if index >= len(self._options):
            return

        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        _, room_type = self._options[index]
        room = run.floor.current_room()
        room.cleared = True

        if room_type == ENEMY:
            # Spawn a random enemy from this floor
            from ..dungeon.enemies import enemies_for_floor
            enemies = enemies_for_floor(run.floor.number, run.biome)
            if enemies:
                enemy = random.choice(enemies)
                room.enemy = dict(enemy)
                app.notify("An enemy emerges from the darkness!", severity="warning", timeout=2)
                app.start_combat(room.enemy)
                return

        elif room_type == TREASURE:
            loot = run.generate_treasure()
            app.notify("You found treasure!", timeout=2)
            app.show_loot(loot)
            return

        elif room_type == TRAP:
            damage, msg = run.apply_trap(app.state.stats.as_dict())
            app.notify(msg, title="Trap!", severity="warning", timeout=3)
            if not run.alive:
                app.dungeon_death()
                return

        elif room_type == REST:
            healed = run.rest(app.state.stats.as_dict())
            app.notify(f"A hidden rest spot! Healed {healed} HP.", timeout=3)

        app.show_dungeon()

    def action_choose_1(self) -> None:
        self._resolve(0)

    def action_choose_2(self) -> None:
        self._resolve(1)

    def action_back(self) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        app.show_dungeon()
