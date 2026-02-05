# Module for diversity
from .interfaces import Scorer, Score


class DiversityScorer(Scorer):
    def __init__(self, penalty: float = 0.1):
        self.penalty = penalty

    def score(self, ctx, candidate) -> Score:
        return Score(value=0.0)
