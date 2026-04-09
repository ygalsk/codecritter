"""In-dungeon shop screen — buy items mid-run with dungeon gold."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from ..constants import C, RARITY_COLORS
from ..dungeon.items import items_by_rarity

if TYPE_CHECKING:
    from ..app import CodecritterApp


MAP_REVEAL_COST = 20


class DungeonShopScreen(Screen):
    """Buy items from a dungeon vendor."""

    BINDINGS = [
        ("1", "buy_1", "Buy #1"),
        ("2", "buy_2", "Buy #2"),
        ("3", "buy_3", "Buy #3"),
        ("m", "buy_map", "Map Reveal"),
        ("escape", "back", "Back"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._stock: list[dict] = []
        self._generate_stock()

    def _generate_stock(self) -> None:
        """Generate 3 random items for sale."""
        # 2 consumables + 1 random gear
        consumables = items_by_rarity("common") + items_by_rarity("uncommon")
        consumable_pool = [i for i in consumables if i.get("type") == "consumable"]
        gear_pool = items_by_rarity("common") + items_by_rarity("uncommon")
        gear_pool = [i for i in gear_pool if i.get("type") != "consumable"]

        stock = []
        if consumable_pool:
            stock.extend(random.sample(consumable_pool, min(2, len(consumable_pool))))
        if gear_pool:
            stock.append(random.choice(gear_pool))

        # Mark up prices slightly for dungeon shop
        for item in stock:
            item = dict(item)
            item["shop_price"] = int(item.get("value", 10) * 1.5)
            self._stock.append(item)

    def compose(self) -> ComposeResult:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run

        with Vertical(id="dungeon-shop-box") as box:
            box.border_title = " DUNGEON SHOP "

            yield Label(f"  [{C.WARNING} bold]═══  WANDERING MERCHANT  ═══[/]", classes="mt1")
            yield Label("")

            if run:
                yield Label(f"  [{C.WARNING}]Your Gold: {run.gold_earned + run.banked_gold}[/]")
            yield Label("")

            for i, item in enumerate(self._stock, 1):
                color = RARITY_COLORS.get(item.get("rarity", ""), "white")
                price = item.get("shop_price", item.get("value", 10))
                yield Label(
                    f"  [{C.ACCENT} bold][{i}][/] "
                    f"[{color} bold]{item.get('name', '?')}[/]  "
                    f"[{C.WARNING}]{price}g[/]  "
                    f"[{C.MUTED}]{item.get('description', '')}[/]"
                )

            yield Label("")
            yield Label(
                f"  [{C.ACCENT} bold][M][/] "
                f"[bold]Reveal Full Map[/]  "
                f"[{C.WARNING}]{MAP_REVEAL_COST}g[/]  "
                f"[{C.MUTED}]Shows all rooms on this floor[/]"
            )

            yield Label("")
            yield Label(f"  [{C.MUTED}][ESC] Leave shop[/]")

        yield Footer()

    def _try_buy(self, index: int) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run or index >= len(self._stock):
            return

        item = self._stock[index]
        price = item.get("shop_price", item.get("value", 10))

        # Spend from un-banked gold first
        if run.gold_earned >= price:
            run.gold_earned -= price
        elif run.gold_earned + run.banked_gold >= price:
            remainder = price - run.gold_earned
            run.gold_earned = 0
            run.banked_gold -= remainder
        else:
            app.notify("Not enough gold!", severity="warning", timeout=2)
            return

        # Add to inventory
        clean_item = {k: v for k, v in item.items() if k != "shop_price"}
        if app.state.inventory_add(clean_item):
            app.notify(f"Bought {item['name']}!", timeout=2)
        else:
            # Refund
            run.gold_earned += price
            app.notify("Inventory full!", severity="warning", timeout=2)

    def action_buy_1(self) -> None:
        self._try_buy(0)

    def action_buy_2(self) -> None:
        self._try_buy(1)

    def action_buy_3(self) -> None:
        self._try_buy(2)

    def action_buy_map(self) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        run = app.dungeon_run
        if not run:
            return

        total_gold = run.gold_earned + run.banked_gold
        if total_gold < MAP_REVEAL_COST:
            app.notify("Not enough gold!", severity="warning", timeout=2)
            return

        if run.gold_earned >= MAP_REVEAL_COST:
            run.gold_earned -= MAP_REVEAL_COST
        else:
            remainder = MAP_REVEAL_COST - run.gold_earned
            run.gold_earned = 0
            run.banked_gold -= remainder

        # Reveal all rooms
        for row in run.floor.rooms:
            for room in row:
                room.explored = True

        app.notify("Map revealed!", timeout=2)

    def action_back(self) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        app.show_dungeon()
