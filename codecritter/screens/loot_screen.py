"""Loot screen — shown when finding treasure or winning a battle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from ..constants import C, RARITY_COLORS

if TYPE_CHECKING:
    from ..app import CodecritterApp


class LootScreen(Screen):
    """Display loot from treasure or battle."""

    def __init__(self, loot: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self._loot = loot

    def compose(self) -> ComposeResult:
        loot = self._loot

        with Vertical(id="loot-box") as box:
            box.border_title = " LOOT "

            yield Label(f"  [{C.WARNING} bold]========  VICTORY  ========[/]", classes="mt1")
            yield Label("")

            # Gold
            gold = loot.get("gold", 0)
            if gold > 0:
                yield Label(f"  [{C.WARNING} bold]+{gold} Gold[/]")

            # XP
            xp = loot.get("xp", 0)
            if xp > 0:
                yield Label(f"  [{C.PRIMARY} bold]+{xp} XP[/]")

            yield Label("")

            # Items
            items = loot.get("items", [])
            if "item" in loot and loot["item"]:
                items = [loot["item"]]

            if items:
                yield Label(f"  [bold]Items found:[/]")
                yield Label("")
                for item in items:
                    color = RARITY_COLORS.get(item.get("rarity", ""), "white")
                    rarity = item.get("rarity", "").upper()
                    yield Label(f"    [{color} bold]{item.get('name', '?')}[/]  [{color}]({rarity})[/]")
                    desc = item.get("description", "")
                    if desc:
                        yield Label(f"    [{C.MUTED}]{desc}[/]")
                    yield Label("")

                yield Label(f"  [{C.MUTED}]Items added to inventory.[/]")
            else:
                yield Label(f"  [{C.MUTED}]No items found.[/]")

            # Dropped items warning
            dropped = loot.get("_dropped", [])
            if dropped:
                yield Label("")
                names = ", ".join(i.get("name", "?") for i in dropped)
                yield Label(f"  [{C.ERROR} bold]Inventory full! Dropped: {names}[/]")

            yield Label("")
            yield Label(f"  [{C.ACCENT} bold]Press any key to continue[/]")

        yield Footer()

    def on_key(self, event) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        app.show_dungeon()
