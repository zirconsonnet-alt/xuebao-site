# Module for bundles
from typing import Iterable, List
from .interfaces import Scorer, Score


class ScoreBundle(Scorer):
    def __init__(self, scorers: Iterable[Scorer]):
        self.scorers = list(scorers)

    def score(self, ctx, candidate) -> Score:
        total = 0.0
        for s in self.scorers:
            total += s.score(ctx, candidate).value
        return Score(value=total)
