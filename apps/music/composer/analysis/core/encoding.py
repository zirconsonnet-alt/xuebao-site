# Module for encoding
from typing import FrozenSet, Iterable, List, Sequence, TypeVar

T = TypeVar("T")


def multi_hot(items: FrozenSet[T] | Iterable[T], order: Sequence[T]) -> List[float]:
    s = set(items)
    return [1.0 if x in s else 0.0 for x in order]


def scalar(x: float) -> List[float]:
    return [float(x)]


def count(items: FrozenSet[T] | Iterable[T]) -> List[float]:
    return [float(len(set(items)))]
