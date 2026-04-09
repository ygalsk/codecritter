"""Dungeon crawler map screen — explore the Code Dungeon."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from ..constants import C
from ..dungeon.generator import BOSS, EMPTY, ENEMY, ENTRANCE, REST, STAIRS, TRAP, TREASURE
from ..widgets.dungeon_map import DungeonMap

if TYPE_CHECKING:
    from ..app import JambApp


class DungeonScreen(Screen):
    """Main dungeon exploration screen with map and movement."""

    BINDINGS = [
        ("w", "move_up", "Up"),
        ("up", "move_up", "Up"),
        ("s", "move_down", "Down"),
        ("down", "move_down", "Down"),
        ("a", "move_left", "Left"),
        ("left", "move_left", "Left"),
        ("d", "move_right", "Right"),
        ("right", "move_right", "Right"),
        ("i", "inventory", "Inventory"),
        ("escape", "flee_dungeon", "Flee"),
    ]

    def compose(self) -> ComposeResult:
        app: JambApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        w = run.floor.width if run else 5
        h = run.floor.height if run else 5

        with Vertical(id="dungeon-box") as box:
            box.border_title = " CODE DUNGEON "

            # Status bar
            with Horizontal(id="dungeon-status-row"):
                yield Label("", id="floor-info")
                yield Label("", id="hp-info")
                yield Label("", id="gold-info")
                yield Label("", id="xp-info")

            # Grid map — fills available space
            yield DungeonMap(width=w, height=h, id="dungeon-grid")

            # Room description
            with Vertical(id="room-panel") as rp:
                rp.border_title = " Room "
                yield Label("", id="room-desc")

            # Legend
            yield Label("", id="dungeon-legend")

        yield Footer()

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        floor = run.floor

        # Status bar
        self.query_one("#floor-info", Label).update(
            f"  [bold]Floor {floor.number}[/]"
        )
        self.query_one("#hp-info", Label).update(
            f"[{C.ERROR}]HP: {run.hp}/{run.max_hp}[/]"
        )
        self.query_one("#gold-info", Label).update(
            f"[{C.WARNING}]Gold: {run.gold_earned}[/]"
        )
        self.query_one("#xp-info", Label).update(
            f"[{C.PRIMARY}]XP: {run.xp_earned}[/]"
        )

        # Update grid map
        grid = self.query_one("#dungeon-grid", DungeonMap)
        grid.update_from_floor(floor)

        # Room description
        room = floor.current_room()
        desc = room.description or "An empty room."
        room_type_label = {
            ENEMY: f"[{C.ERROR} bold]ENEMY[/]",
            BOSS: f"[{C.ERROR} bold]BOSS[/]",
            TREASURE: f"[{C.WARNING} bold]TREASURE[/]",
            REST: f"[{C.SECONDARY} bold]REST POINT[/]",
            TRAP: f"[{C.PRIMARY} bold]TRAP[/]",
            STAIRS: f"[{C.PRIMARY} bold]STAIRS DOWN[/]",
        }.get(room.room_type if not room.cleared else EMPTY, "")

        self.query_one("#room-desc", Label).update(
            f"  {room_type_label} {desc}" if room_type_label else f"  {desc}"
        )

        # Legend
        self.query_one("#dungeon-legend", Label).update(
            f"  [{C.SUCCESS}]@[/]=You  [{C.ERROR}]![/]=Enemy  [{C.ERROR}]B[/]=Boss  "
            f"[{C.WARNING}]?[/]=Loot  [{C.SECONDARY}]+[/]=Rest  [{C.PRIMARY}]^[/]=Trap  "
            f"[{C.PRIMARY}]>[/]=Stairs  [{C.MUTED}]░[/]=Unknown"
        )

    def _handle_room(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        room = run.floor.current_room()

        if room.room_type in (ENEMY, BOSS) and not room.cleared:
            app.start_combat(room.enemy)
        elif room.room_type == TREASURE and not room.cleared:
            room.cleared = True
            loot = run.generate_treasure()
            app.show_loot(loot)
        elif room.room_type == REST and not room.cleared:
            room.cleared = True
            healed = run.rest()
            app.notify(f"Rested! Healed {healed} HP.", title="Rest Point", timeout=3)
            self._refresh()
        elif room.room_type == TRAP and not room.cleared:
            room.cleared = True
            damage, msg = run.apply_trap(app.state.stats.as_dict())
            app.notify(msg, title="Trap!", severity="warning", timeout=3)
            if not run.alive:
                app.dungeon_death()
            else:
                self._refresh()
        elif room.room_type == STAIRS:
            run.next_floor()
            app.notify(
                f"Descending to Floor {run.floor.number}...",
                title="Deeper!",
                timeout=2,
            )
            self._refresh()
        else:
            self._refresh()

    def _move(self, dx: int, dy: int) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        room = run.floor.move_player(dx, dy)
        if room:
            self._handle_room()
        else:
            self._refresh()

    def action_move_up(self) -> None:
        self._move(0, -1)

    def action_move_down(self) -> None:
        self._move(0, 1)

    def action_move_left(self) -> None:
        self._move(-1, 0)

    def action_move_right(self) -> None:
        self._move(1, 0)

    def action_inventory(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        app.show_inventory()

    def action_flee_dungeon(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        app.end_dungeon(fled=True)
