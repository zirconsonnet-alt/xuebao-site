# Module for rerank policy
from typing import Sequence
from ..interfaces import PolicyModel, ScoredCandidate


class RerankPolicy(PolicyModel):
    def choose(self, ctx, candidates: Sequence[ScoredCandidate]):
        items = list(candidates)
        if not items:
            raise ValueError("no candidates")
        items.sort(key=lambda c: c.score, reverse=True)
        return items[0].obj
