"""Extraction point screen — bank loot safely or leave the dungeon."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Label

from ..constants import C
from .base import CodecritterScreen


class ExtractionScreen(CodecritterScreen):
    """Bank loot at an extraction point, or bank and leave."""

    BINDINGS = [
        ("b", "bank_continue", "Bank & Continue"),
        ("l", "bank_leave", "Bank & Leave"),
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        run = self.capp.dungeon_run

        with Vertical(id="extraction-box") as box:
            box.border_title = " EXTRACTION POINT "

            yield Label(f"  [{C.SUCCESS} bold]═══  SECURE BACKUP TERMINAL  ═══[/]", classes="mt1")
            yield Label("")

            if run:
                yield Label(f"  [{C.WARNING}]Un-banked Gold: {run.gold_earned}[/]")
                yield Label(f"  [{C.WARNING}]Un-banked Items: {len(run.items_found)}[/]")
                yield Label("")
                yield Label(f"  [{C.SUCCESS}]Banked Gold: {run.banked_gold}[/]")
                yield Label(f"  [{C.SUCCESS}]Banked Items: {len(run.banked_items)}[/]")
                yield Label("")
                yield Label(f"  [{C.MUTED}]Banked loot is safe from death.[/]")
                yield Label(f"  [{C.MUTED}]Un-banked loot is lost if defeated.[/]")
            else:
                yield Label(f"  [{C.MUTED}]No active dungeon run.[/]")

            yield Label("")
            yield Label(f"  [{C.ACCENT} bold][B][/] Bank loot & continue deeper")
            yield Label(f"  [{C.ACCENT} bold][L][/] Bank loot & leave dungeon")
            yield Label(f"  [{C.MUTED}][ESC][/] Go back without banking")

        yield Footer()

    def action_bank_continue(self) -> None:
        run = self.capp.dungeon_run
        if run:
            gold, items = run.bank_loot()
            self.capp.notify(
                f"Banked {gold} gold and {items} items!",
                title="Loot Secured",
                timeout=3,
            )
        self.capp.show_dungeon()

    def action_bank_leave(self) -> None:
        run = self.capp.dungeon_run
        if run:
            run.bank_loot()
        self.capp.end_dungeon(fled=True)

    def action_back(self) -> None:
        self.capp.show_dungeon()
