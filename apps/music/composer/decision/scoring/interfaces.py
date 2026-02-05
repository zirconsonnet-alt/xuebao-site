# Module for interfaces
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Score:
    value: float
    evidence: Optional[Any] = None


class Scorer:
    def score(self, ctx, candidate) -> Score:
        raise NotImplementedError
