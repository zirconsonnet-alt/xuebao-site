# Module for weighted policy
import random
from typing import Sequence
from ..interfaces import PolicyModel, ScoredCandidate


class WeightedPolicy(PolicyModel):
    def choose(self, ctx, candidates: Sequence[ScoredCandidate]):
        items = list(candidates)
        if not items:
            raise ValueError('no candidates')
        values = [c.score for c in items]
        total = sum(values)
        if total <= 0:
            return random.choice([c.obj for c in items])
        r = random.random() * total
        acc = 0.0
        for cand in items:
            acc += cand.score
            if acc >= r:
                return cand.obj
        return items[-1].obj
