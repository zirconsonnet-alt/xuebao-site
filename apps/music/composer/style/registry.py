# Module for registry
from typing import Dict, Optional
from .profile import StyleProfile


class StyleRegistry:
    def __init__(self) -> None:
        self._styles: Dict[str, StyleProfile] = {}

    def register(self, style: StyleProfile) -> None:
        self._styles[style.name] = style

    def get(self, name: str) -> Optional[StyleProfile]:
        return self._styles.get(name)
