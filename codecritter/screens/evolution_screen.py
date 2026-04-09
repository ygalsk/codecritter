from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Label

from ..constants import C, EVOLUTION_MESSAGES, EVOLUTION_NAMES, SPECIES_EVOLUTION
from ..widgets.ascii_art import SnailArt

if TYPE_CHECKING:
    from ..app import CodecritterApp


class EvolutionScreen(Screen):
    """One-time evolution announcement overlay."""

    def __init__(self, new_stage: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._new_stage = new_stage

    def compose(self) -> ComposeResult:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        state = app.state
        new_stage = self._new_stage

        spec = state.stats.highest() if new_stage == "adult" else None
        sp_key = state.species.lower()
        if sp_key in SPECIES_EVOLUTION and new_stage in SPECIES_EVOLUTION[sp_key]:
            stage_names = SPECIES_EVOLUTION[sp_key][new_stage]
        else:
            stage_names = EVOLUTION_NAMES.get(new_stage, {})
        form_name = stage_names.get(spec or "default", stage_names.get("default", new_stage.title()))

        with Vertical(classes="evolution-container") as vc:
            vc.border_title = " EVOLUTION "
            yield Label(f"  [{C.ACCENT} bold]* * *  EVOLUTION!  * * *[/]", classes="mt1")
            yield Label(f"  [{C.SECONDARY}]{EVOLUTION_MESSAGES[0]}[/]", classes="mt1")
            yield Label(f"  [{C.SECONDARY}]{EVOLUTION_MESSAGES[1]}[/]")
            with Horizontal(id="art-speech"):
                yield SnailArt(new_stage, spec, species=state.species.lower(), eyes=state.eyes or "·", id="snail-art")
                yield Label("")
            yield Label(f"  [{C.SUCCESS} bold]Jamb evolved into: {form_name}![/]", classes="mt1")
            yield Label(f"  Stage: {new_stage.title()}  |  Level {state.level}", classes="dim")
            yield Label(f"  [{C.ACCENT} bold]Press any key to continue[/]", classes="mt1")

        yield Footer()

    def on_key(self, event) -> None:
        app: CodecritterApp = self.app  # type: ignore[assignment]
        app.show_main()
