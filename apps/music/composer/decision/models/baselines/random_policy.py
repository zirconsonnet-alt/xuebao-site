# Module for random policy
import random
from typing import Sequence
from ..interfaces import PolicyModel, ScoredCandidate


class RandomPolicy(PolicyModel):
    def choose(self, ctx, candidates: Sequence[ScoredCandidate]):
        return random.choice(list(candidates)).obj
