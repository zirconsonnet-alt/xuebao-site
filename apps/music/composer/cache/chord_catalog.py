# Module for chord catalog
from typing import Dict, List


class ChordCatalog:
    def __init__(self) -> None:
        self._items: Dict[str, List[str]] = {}

    def add(self, key: str, chords: List[str]) -> None:
        self._items[key] = chords

    def get(self, key: str) -> List[str]:
        return self._items.get(key, [])
