from __future__ import annotations

import time

from textual.message import Message
from textual.widgets import Static

from ..constants import mood_style

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

    class Changed(Message):
        """Posted when the displayed speech text changes."""
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self, mood: str = "happy", **kwargs) -> None:
        self._mood = mood
        self._reaction: str | None = None
        self._reaction_ts: float | None = None
        initial_text = self._current_text()
        self._last_text: str = initial_text
        super().__init__(initial_text, **kwargs)

    def on_mount(self) -> None:
        self.border_title = MOOD_ICONS.get(self._mood, "Jamb says...")
        self.add_class(mood_style(self._mood))
        # Sync initial text to statusline
        self.post_message(self.Changed(self._last_text))

    def _current_text(self) -> str:
        """Show active reaction if recent, otherwise a static default."""
        if self._reaction and self._reaction_ts:
            if (time.time() - self._reaction_ts) < REACTION_TTL:
                return f'💬 {self._reaction}'
        return "..."

    def _emit(self, text: str) -> None:
        """Post Changed message if text actually differs."""
        if text != self._last_text:
            self._last_text = text
            self.post_message(self.Changed(text))

    def set_reaction(self, text: str | None, ts: float | None) -> None:
        """Update the displayed reaction from state."""
        self._reaction = text
        self._reaction_ts = ts
        new_text = self._current_text()
        self.update(new_text)
        self._emit(new_text)

