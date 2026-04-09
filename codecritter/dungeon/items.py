"""Item definitions for the Code Dungeon.

Thin wrapper over data_loader — all content lives in JSON.
"""

from __future__ import annotations

from . import data_loader


def get_item(item_id: str) -> dict | None:
    """Look up a single item by id."""
    return data_loader.get_item(item_id)


def items_by_rarity(rarity: str) -> list[dict]:
    """Get all items of a given rarity."""
    return data_loader.get_items_by_rarity(rarity)


# ── Backwards compatibility ─────────────────────────────────────────
# engine.py and other modules import ITEMS_BY_ID and CONSUMABLES directly.

class _LazyDict:
    """Dict-like wrapper that loads on first access."""
    def __init__(self, loader):
        self._loader = loader
        self._data = None

    def _ensure(self):
        if self._data is None:
            self._data = self._loader()

    def get(self, key, default=None):
        self._ensure()
        return self._data.get(key, default)

    def __getitem__(self, key):
        self._ensure()
        return self._data[key]

    def __contains__(self, key):
        self._ensure()
        return key in self._data

    def __iter__(self):
        self._ensure()
        return iter(self._data)

    def values(self):
        self._ensure()
        return self._data.values()

    def items(self):
        self._ensure()
        return self._data.items()


class _LazyList:
    """List-like wrapper that loads on first access."""
    def __init__(self, loader):
        self._loader = loader
        self._data = None

    def _ensure(self):
        if self._data is None:
            self._data = self._loader()

    def __iter__(self):
        self._ensure()
        return iter(self._data)

    def __len__(self):
        self._ensure()
        return len(self._data)

    def __getitem__(self, idx):
        self._ensure()
        return self._data[idx]


ITEMS_BY_ID = _LazyDict(data_loader.get_items_by_id)
CONSUMABLES = _LazyList(lambda: data_loader.load_items().get("consumables", []))
ALL_ITEMS = _LazyList(data_loader.get_all_items)

# Category lists
WEAPONS = _LazyList(lambda: data_loader.load_items().get("weapons", []))
ARMORS = _LazyList(lambda: data_loader.load_items().get("armors", []))
ACCESSORIES = _LazyList(lambda: data_loader.load_items().get("accessories", []))
