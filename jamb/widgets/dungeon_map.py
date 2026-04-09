"""Grid-based dungeon map widget — fills available space with colored cells."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static

from ..constants import C
from ..dungeon.generator import (
    BOSS, EMPTY, ENEMY, ENTRANCE, REST, STAIRS, TRAP, TREASURE, WALL, Floor,
)

# Room type -> (symbol, Rich color, CSS class suffix)
CELL_STYLES: dict[str, tuple[str, str, str]] = {
    ENEMY:    ("!", C.ERROR,     "enemy"),
    BOSS:     ("B", C.ERROR,     "boss"),
    TREASURE: ("?", C.WARNING,   "treasure"),
    REST:     ("+", C.SECONDARY, "rest"),
    TRAP:     ("^", C.PRIMARY,   "trap"),
    STAIRS:   (">", C.PRIMARY,   "stairs"),
    WALL:     ("#", C.MUTED,     "wall"),
    EMPTY:    ("·", C.MUTED,     "cleared"),
    ENTRANCE: ("·", C.MUTED,     "cleared"),
}


class MapCell(Static):
    """A single room cell in the dungeon map."""

    DEFAULT_CSS = """
    MapCell {
        width: 1fr;
        height: 1fr;
        content-align: center middle;
        text-align: center;
        border: solid $panel;
    }
    MapCell.cell-player    { border: solid $success; background: $success 15%; }
    MapCell.cell-enemy     { border: solid $error; }
    MapCell.cell-boss      { border: heavy $error; background: $error 8%; }
    MapCell.cell-treasure  { border: solid $warning; }
    MapCell.cell-rest      { border: solid $secondary; }
    MapCell.cell-trap      { border: solid $primary; }
    MapCell.cell-stairs    { border: double $primary; }
    MapCell.cell-unexplored { border: solid $surface; }
    MapCell.cell-cleared   { border: solid $panel; }
    MapCell.cell-wall      { border: solid $surface; background: $surface; }
    """

    def __init__(self, x: int, y: int, **kwargs) -> None:
        super().__init__("", id=f"cell-{x}-{y}", **kwargs)
        self.cell_x = x
        self.cell_y = y


class DungeonMap(Container):
    """Grid container of MapCells that fills available space."""

    DEFAULT_CSS = """
    DungeonMap {
        layout: grid;
        grid-gutter: 0;
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self, width: int = 5, height: int = 5, **kwargs) -> None:
        super().__init__(**kwargs)
        self._map_w = width
        self._map_h = height

    def compose(self):
        for y in range(self._map_h):
            for x in range(self._map_w):
                yield MapCell(x, y)

    def on_mount(self) -> None:
        # Set grid size dynamically based on map dimensions
        self.styles.grid_size_columns = self._map_w
        self.styles.grid_size_rows = self._map_h

    def update_from_floor(self, floor: Floor) -> None:
        """Refresh all cells from floor state."""
        for y in range(floor.height):
            for x in range(floor.width):
                cell = self.query_one(f"#cell-{x}-{y}", MapCell)
                room = floor.rooms[y][x]
                is_player = (x == floor.player_x and y == floor.player_y)

                # Clear old classes
                for cls in list(cell.classes):
                    if cls.startswith("cell-"):
                        cell.remove_class(cls)

                if is_player:
                    cell.update(f"[bold {C.SUCCESS}]@[/]")
                    cell.add_class("cell-player")
                elif not room.explored:
                    cell.update(f"[{C.MUTED}]░[/]")
                    cell.add_class("cell-unexplored")
                elif room.room_type == WALL:
                    cell.update("")
                    cell.add_class("cell-wall")
                elif room.cleared or room.room_type in (EMPTY, ENTRANCE):
                    cell.update(f"[{C.MUTED}]·[/]")
                    cell.add_class("cell-cleared")
                else:
                    sym, color, css_cls = CELL_STYLES.get(
                        room.room_type, ("?", C.MUTED, "cleared")
                    )
                    cell.update(f"[bold {color}]{sym}[/]")
                    cell.add_class(f"cell-{css_cls}")
