# Module for registry
from typing import Dict, Optional
from .analyzer import Analyzer
from .kinds import ResolveKind


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._registry: Dict[ResolveKind, Analyzer] = {}

    def register(self, kind: ResolveKind, analyzer: Analyzer) -> None:
        self._registry[kind] = analyzer

    def get(self, kind: ResolveKind) -> Optional[Analyzer]:
        return self._registry.get(kind)
