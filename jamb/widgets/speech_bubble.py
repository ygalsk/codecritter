from __future__ import annotations

import random
import time

from textual.widgets import Static

from ..constants import QUIPS, mood_style

MOOD_ICONS: dict[str, str] = {
    "ecstatic": "★ Jamb is ECSTATIC",
    "happy": "☺ Jamb says...",
    "content": "◉ Jamb says...",
    "bored": "… Jamb sighs...",
    "hungry": "◉ Jamb grumbles...",
    "tired": "☽ Jamb mumbles...",
    "grumpy": "☠ Jamb growls...",
    "chaotic": "⚡ Jamb shrieks...",
}

# How long a reaction stays visible before falling back to quips (seconds)
REACTION_TTL = 60.0


class SpeechBubble(Static):
    """A speech bubble that shows mood-themed quips or active reactions."""

    def __init__(self, mood: str = "happy", **kwargs) -> None:
        self._mood = mood
        self._reaction: str | None = None
        self._reaction_ts: float | None = None
        super().__init__(self._current_text(), **kwargs)

    def on_mount(self) -> None:
        self.border_title = MOOD_ICONS.get(self._mood, "Jamb says...")
        self.add_class(mood_style(self._mood))

    def _random_quip(self) -> str:
        pool = QUIPS.get(self._mood, QUIPS["content"])
        return f'"{random.choice(pool)}"'

    def _current_text(self) -> str:
        """Show active reaction if recent, otherwise a random quip."""
        if self._reaction and self._reaction_ts:
            if (time.time() - self._reaction_ts) < REACTION_TTL:
                return f'💬 {self._reaction}'
        return self._random_quip()

    def set_reaction(self, text: str | None, ts: float | None) -> None:
        """Update the displayed reaction from state."""
        self._reaction = text
        self._reaction_ts = ts
        self.update(self._current_text())

    def rotate(self) -> None:
        self.update(self._current_text())
