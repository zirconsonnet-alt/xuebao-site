# Module for registry
from typing import Callable, Dict, Optional, Sequence

from ..core.kinds import ResolveKind


class ResolverRegistry:
    def __init__(self) -> None:
        self._registry: Dict[ResolveKind, Callable[..., Sequence]] = {}

    def register(self, kind: ResolveKind, generator: Callable[..., Sequence]) -> None:
        self._registry[kind] = generator

    def get(self, kind: ResolveKind) -> Optional[Callable[..., Sequence]]:
        return self._registry.get(kind)
