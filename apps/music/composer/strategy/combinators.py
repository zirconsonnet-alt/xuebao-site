# Module for combinators
from typing import Iterable, List
from .interfaces import Strategy


class Chain(Strategy):
    def __init__(self, strategies: Iterable[Strategy]):
        self.strategies: List[Strategy] = list(strategies)

    def build(self, style):
        result = None
        for s in self.strategies:
            result = s.build(style)
        return result
