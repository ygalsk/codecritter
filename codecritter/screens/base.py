"""Base screen with typed app accessor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.screen import Screen

if TYPE_CHECKING:
    from ..app import CodecritterApp


class CodecritterScreen(Screen):
    @property
    def capp(self) -> CodecritterApp:
        return self.app  # type: ignore[return-value]
