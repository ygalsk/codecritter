from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Label, ProgressBar

from ..constants import C, STAT_COLORS
from ..widgets.ascii_art import SnailArt
from ..widgets.speech_bubble import SpeechBubble

if TYPE_CHECKING:
    from ..app import JambApp

STAT_ORDER = ["debugging", "patience", "chaos", "wisdom", "snark"]


class MainScreen(Screen):

    BINDINGS = [
        ("d", "dungeon", "Dungeon"),
        ("i", "inventory", "Inventory"),
        ("s", "shop", "Shop"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        app: JambApp = self.app  # type: ignore[assignment]
        state = app.state

        with VerticalScroll(id="main-box") as main:
            main.border_title = f" {state.name} "

            # Header row: rarity | stage | gold | level
            with Horizontal(id="header-row"):
                yield Label(f"[bold {C.PRIMARY}]{state.rarity}[/]", id="header-rarity")
                yield Label(f"[bold {C.SECONDARY}]{state.stage.title()}[/]", id="header-stage")
                yield Label(f"[{C.WARNING}]{state.gold}g[/]", id="header-gold")
                yield Label(f"Lv [bold]{state.level}[/]/{state.level_cap()}", id="header-level")

            # Art + speech side by side
            spec = state.stats.highest() if state.stage == "adult" else None
            with Horizontal(id="art-speech"):
                yield SnailArt(state.stage, spec, species=state.species.lower(), eyes=state.eyes or "·", id="snail-art")
                yield SpeechBubble("content", id="speech-bubble")

            # Title + XP section
            with Vertical(id="xp-section"):
                yield Label(id="title-xp-line")
                xp_bar = ProgressBar(
                    total=state.xp_to_next_level(),
                    show_eta=False,
                    show_percentage=False,
                    classes="xp-bar",
                    id="xp-bar",
                )
                yield xp_bar

            # Stat bars panel
            stat_dict = state.stats.as_dict()
            cap = state.stat_cap()
            with Vertical(id="stats-panel") as sp:
                sp.border_title = " Stats "
                for stat_name in STAT_ORDER:
                    val = stat_dict.get(stat_name, 0)
                    color = STAT_COLORS[stat_name]
                    with Horizontal(classes="stat-bar-row"):
                        yield Label(f"[{color}]{stat_name.upper()}[/]", classes="stat-bar-label")
                        bar = ProgressBar(
                            total=cap,
                            show_eta=False,
                            show_percentage=False,
                            classes=f"bar-{stat_name}",
                            id=f"bar-{stat_name}",
                        )
                        yield bar
                        yield Label(f"[{color}]{val}[/]/{cap}", classes="stat-bar-value")

        yield Footer()

    def on_mount(self) -> None:
        self._refresh_dynamic()
        app: JambApp = self.app  # type: ignore[assignment]
        state = app.state

        # Set XP bar
        xp_bar = self.query_one("#xp-bar", ProgressBar)
        xp_bar.advance(state.xp)

        # Set stat bars
        stat_dict = state.stats.as_dict()
        for stat_name in STAT_ORDER:
            val = stat_dict.get(stat_name, 0)
            bar = self.query_one(f"#bar-{stat_name}", ProgressBar)
            bar.advance(val)

    def _refresh_dynamic(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        state = app.state

        title_xp = self.query_one("#title-xp-line", Label)
        title_xp.update(
            f"  [{C.ACCENT} bold]{state.title}[/]  |  XP: {state.xp}/{state.xp_to_next_level()}"
        )

    def refresh_state(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        state = app.state

        # Update header
        self.query_one("#header-rarity", Label).update(
            f"[bold {C.PRIMARY}]{state.rarity}[/]"
        )
        self.query_one("#header-stage", Label).update(
            f"[bold {C.SECONDARY}]{state.stage.title()}[/]"
        )
        self.query_one("#header-gold", Label).update(
            f"[{C.WARNING}]{state.gold}g[/]"
        )
        self.query_one("#header-level", Label).update(
            f"Lv [bold]{state.level}[/]/{state.level_cap()}"
        )

        # Update XP
        xp_bar = self.query_one("#xp-bar", ProgressBar)
        xp_bar.update(total=state.xp_to_next_level(), progress=state.xp)

        # Update stat bars
        stat_dict = state.stats.as_dict()
        cap = state.stat_cap()
        for stat_name in STAT_ORDER:
            val = stat_dict.get(stat_name, 0)
            color = STAT_COLORS[stat_name]
            bar = self.query_one(f"#bar-{stat_name}", ProgressBar)
            bar.update(total=cap, progress=val)
            # Update value label — it's the 3rd child in the row
            try:
                row = bar.parent
                value_label = row.query(".stat-bar-value").first()
                value_label.update(f"[{color}]{val}[/]/{cap}")
            except Exception:
                pass

        self._refresh_dynamic()

        # Update border title
        main = self.query_one("#main-box")
        main.border_title = f" {state.name} "

        # Update speech and art
        speech = self.query_one("#speech-bubble", SpeechBubble)
        speech.set_reaction(state.reaction, state.reaction_ts)

        snail = self.query_one("#snail-art", SnailArt)
        spec = state.stats.highest() if state.stage == "adult" else None
        snail.set_stage(state.stage, spec, species=state.species.lower(), eyes=state.eyes or "·")

    def animate_snail(self) -> None:
        try:
            snail = self.query_one("#snail-art", SnailArt)
            snail.next_frame()
        except Exception:
            pass

    def rotate_speech(self) -> None:
        try:
            speech = self.query_one("#speech-bubble", SpeechBubble)
            speech.rotate()
        except Exception:
            pass

    def action_dungeon(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        app.show_dungeon()

    def action_inventory(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        app.show_inventory()

    def action_shop(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        app.show_shop()

    def action_quit_app(self) -> None:
        app: JambApp = self.app  # type: ignore[assignment]
        app.save_and_quit()
