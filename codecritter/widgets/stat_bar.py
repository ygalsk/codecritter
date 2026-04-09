from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, ProgressBar, Static

from ..constants import STAT_COLORS


class StatBar(Static):
    """A labeled stat bar: LABEL  ████░░░░  VALUE"""

    def __init__(
        self, label: str, value: int, max_val: int, bar_class: str,
        base: int | None = None, **kwargs,
    ) -> None:
        self._label_text = label
        self._value = value
        self._max_val = max_val
        self._bar_class = bar_class
        self._base = base
        self._color = STAT_COLORS.get(bar_class.replace("bar-", ""), "white")
        super().__init__(**kwargs)

    def _value_label(self) -> str:
        base_str = f" [dim](+{self._value - self._base})[/]" if self._base is not None else ""
        return f" [{self._color} bold]{self._value:>3}[/][dim]/{self._max_val}[/]{base_str}"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="stat-bar-row"):
            yield Label(f"  [{self._color} bold]{self._label_text:<10}[/]", classes="stat-bar-label")
            bar = ProgressBar(total=self._max_val, show_eta=False, show_percentage=False, classes=self._bar_class)
            bar.advance(self._value)
            yield bar
            yield Label(self._value_label(), classes="stat-bar-value")

    def update_value(self, value: int, max_val: int | None = None, base: int | None = None) -> None:
        self._value = value
        if max_val is not None:
            self._max_val = max_val
        if base is not None:
            self._base = base
        bar = self.query_one(ProgressBar)
        bar.update(total=self._max_val, progress=value)
        val_label = self.query(".stat-bar-value").last()
        val_label.update(self._value_label())
