# Analysis facade
from typing import Any, Optional

from ..core.hit import ResolveHit
from ..core.kinds import ResolveKind
from ..core.registry import AnalyzerRegistry
from ..explain.analyzers.chord_in_mode_analyzer import ChordInModeAnalyzer
from ..explain.analyzers.chord_in_key_analyzer import ChordInKeyAnalyzer
from ..explain.analyzers.mode_in_key_analyzer import ModeInKeyAnalyzer

_DEFAULT_ANALYZER_REGISTRY: Optional[AnalyzerRegistry] = None


def _default_analyzer_registry() -> AnalyzerRegistry:
    global _DEFAULT_ANALYZER_REGISTRY
    if _DEFAULT_ANALYZER_REGISTRY is None:
        registry = AnalyzerRegistry()
        registry.register(ResolveKind.ChordInMode, ChordInModeAnalyzer())
        registry.register(ResolveKind.ChordInKey, ChordInKeyAnalyzer())
        registry.register(ResolveKind.ModeInKey, ModeInKeyAnalyzer())
        _DEFAULT_ANALYZER_REGISTRY = registry
    return _DEFAULT_ANALYZER_REGISTRY


def analyze_hit(hit: ResolveHit) -> Optional[Any]:
    analyzer = _default_analyzer_registry().get(hit.kind)
    if analyzer is None:
        return None
    return analyzer.analyze(hit)
