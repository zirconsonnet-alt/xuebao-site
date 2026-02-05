# Rule checks for rules as scores
from .interfaces import Scorer, Score


class SoftRuleScorer(Scorer):
    def __init__(self, weight: float = 1.0):
        self.weight = weight

    def score(self, ctx, candidate) -> Score:
        return Score(value=0.0)
