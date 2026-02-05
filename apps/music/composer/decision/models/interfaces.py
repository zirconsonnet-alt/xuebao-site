# Module for interfaces
from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    obj: Any
    score: float
    evidence: Optional[Any] = None


class PolicyModel:
    def choose(self, ctx, candidates: Sequence[ScoredCandidate]) -> Any:
        raise NotImplementedError

    def rank(self, ctx, candidates: Sequence[ScoredCandidate]) -> Sequence[ScoredCandidate]:
        return candidates
