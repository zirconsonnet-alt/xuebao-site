# Module for constraints
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class Violation:
    code: str
    message: str


class Constraint:
    def check(self, ctx, candidate) -> Optional[Violation]:
        return None


class AllOf(Constraint):
    def __init__(self, items: Iterable[Constraint]):
        self.items = list(items)

    def check(self, ctx, candidate) -> Optional[Violation]:
        for item in self.items:
            v = item.check(ctx, candidate)
            if v is not None:
                return v
        return None


class AnyOf(Constraint):
    def __init__(self, items: Iterable[Constraint]):
        self.items = list(items)

    def check(self, ctx, candidate) -> Optional[Violation]:
        last = None
        for item in self.items:
            v = item.check(ctx, candidate)
            if v is None:
                return None
            last = v
        return last
