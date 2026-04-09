"""Dungeon crawler map screen — explore the Code Dungeon."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from ..constants import C
from ..dungeon.generator import (
    BOSS, CURSED_CHEST, EMPTY, ENEMY, ENTRANCE, EXTRACTION, FORK,
    REST, SHOP, STAIRS, TRAP, TREASURE,
)
from ..widgets.dungeon_map import DungeonMap

if TYPE_CHECKING:
    from ..app import CodecritterApp


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
        app: CodecritterApp = self.app  # type: ignore[assignment]
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
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        floor = run.floor

        # Status bar
        from ..dungeon import data_loader
        biome_data = data_loader.load_biome(run.biome)
        biome_name = biome_data.get("name", "Code Dungeon")
        modifier_label = ""
        if run.floor_modifier:
            mod_name = run.floor_modifier.get("name", "")
            modifier_label = f"  [bold #FF9E64]⚡{mod_name}[/]"

        self.query_one("#floor-info", Label).update(
            f"  [bold]Floor {floor.number}[/]  [{C.MUTED}]{biome_name}[/]{modifier_label}"
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
            SHOP: f"[{C.WARNING} bold]SHOP[/]",
            FORK: f"[{C.SECONDARY} bold]FORK[/]",
            EXTRACTION: f"[{C.SUCCESS} bold]EXTRACTION[/]",
            CURSED_CHEST: f"[{C.ERROR} bold]CURSED CHEST[/]",
        }.get(room.room_type if not room.cleared else EMPTY, "")

        self.query_one("#room-desc", Label).update(
            f"  {room_type_label} {desc}" if room_type_label else f"  {desc}"
        )

        # Legend
        self.query_one("#dungeon-legend", Label).update(
            f"  [{C.SUCCESS}]@[/]=You  [{C.ERROR}]![/]=Enemy  [{C.ERROR}]B[/]=Boss  "
            f"[{C.WARNING}]?[/]=Loot  [{C.SECONDARY}]+[/]=Rest  [{C.PRIMARY}]^[/]=Trap  "
            f"[{C.PRIMARY}]>[/]=Stairs  [{C.WARNING}]$[/]=Shop  "
            f"[{C.SECONDARY}]Y[/]=Fork  [{C.SUCCESS}]E[/]=Extract  [{C.ERROR}]C[/]=Cursed"
        )

    def _handle_room(self) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
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
            healed = run.rest(app.state.stats.as_dict())
            app.notify(f"Rested! Healed {healed} HP.", title="Rest Point", timeout=3)
            self._refresh()
        elif room.room_type == TRAP and not room.cleared:
            room.cleared = True
            damage, msg = run.apply_trap(app.state.stats.as_dict(), trap=room.trap)
            app.notify(msg, title="Trap!", severity="warning", timeout=3)
            if not run.alive:
                app.dungeon_death()
            else:
                self._refresh()
        elif room.room_type == STAIRS:
            run.next_floor(stats=app.state.stats.as_dict())
            modifier_msg = ""
            if run.floor_modifier:
                modifier_msg = f" ⚡{run.floor_modifier.get('name', '')}: {run.floor_modifier.get('description', '')}"
            app.notify(
                f"Descending to Floor {run.floor.number}...{modifier_msg}",
                title="Deeper!",
                timeout=3,
            )
            self._refresh()
        elif room.room_type == SHOP and not room.cleared:
            room.cleared = True
            app.show_dungeon_shop()
        elif room.room_type == EXTRACTION and not room.cleared:
            room.cleared = True
            app.show_extraction()
        elif room.room_type == FORK and not room.cleared:
            if room.fork_options:
                app.show_fork(room.fork_options)
            else:
                room.cleared = True
                self._refresh()
        elif room.room_type == CURSED_CHEST and not room.cleared:
            room.cleared = True
            self._handle_cursed_chest()
        else:
            self._refresh()

    def _handle_cursed_chest(self) -> None:
        """Open a cursed chest — 60% rare loot, 40% curse."""
        import random
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        if random.random() < 0.6:
            # Good loot — force rare/legendary
            from ..dungeon.items import items_by_rarity
            pool = items_by_rarity("rare") + items_by_rarity("legendary")
            if pool:
                item = random.choice(pool)
                gold = random.randint(15, 40)
                run.gold_earned += gold
                app.notify("The chest reveals rare loot!", title="Lucky!", timeout=3)
                app.show_loot({"item": dict(item), "gold": gold})
            else:
                self._refresh()
        else:
            # Curse — temporary debuff
            curses = [
                ("Max HP reduced by 10%", "hp"),
                ("Attack reduced by 2", "attack"),
                ("Defense reduced by 1", "defense"),
            ]
            curse_name, curse_type = random.choice(curses)
            if curse_type == "hp":
                reduction = run.max_hp // 10
                run.max_hp -= reduction
                run.hp = min(run.hp, run.max_hp)
            elif curse_type == "attack":
                pass  # Applied in next combat
            elif curse_type == "defense":
                pass  # Applied in next combat
            app.notify(
                f"CURSED! {curse_name} (until next rest)",
                title="Curse!",
                severity="warning",
                timeout=4,
            )
            self._refresh()

    def _move(self, dx: int, dy: int) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        # Fog modifier: don't reveal adjacent rooms
        is_fog = (run.floor_modifier or {}).get("id") == "fog"
        if is_fog:
            room = run.floor.move_player_fog(dx, dy)
        else:
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
        app: CodecritterApp = self.app  # type: ignore[assignment]
        app.show_inventory()

    def action_flee_dungeon(self) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        app.end_dungeon(fled=True)
