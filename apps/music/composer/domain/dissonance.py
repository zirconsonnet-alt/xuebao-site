from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, FrozenSet, Iterable, Tuple

from .enums.core import Degrees, Intervals


class Resolution(Enum):
    NONE = auto()
    STEP_UP = auto()
    STEP_DOWN = auto()
    STEP_EITHER = auto()


@dataclass(frozen=True, slots=True)
class DissonanceRelation:
    notes: FrozenSet[Intervals]
    kind: str
    priority: int
    min_moves: int
    resolution: Tuple[Tuple[Intervals, Resolution], ...]

    def __post_init__(self) -> None:
        if self.min_moves < 0:
            raise ValueError("min_moves 必须 >= 0")
        movable = sum(1 for _, r in self.resolution if r != Resolution.NONE)
        if self.min_moves > movable:
            raise ValueError("min_moves 不能大于可移动音数量")

    def resolution_map(self) -> Dict[Intervals, Resolution]:
        return dict(self.resolution)


@dataclass(frozen=True, slots=True)
class EdgeRule:
    delta_semitones: int
    kind: str
    priority: int
    earlier_resolution: Resolution
    later_resolution: Resolution
    min_moves: int = 1


@dataclass(frozen=True, slots=True)
class SetRule:
    kind: str
    priority: int
    min_moves: int
    match: Callable[[FrozenSet[int]], bool]
    resolution_for_member: Callable[[Intervals], Resolution]


TERTIAN_STACK_ORDER: Tuple[Degrees, ...] = (
    Degrees.I,
    Degrees.III,
    Degrees.V,
    Degrees.VII,
    Degrees.II,
    Degrees.IV,
    Degrees.VI,
)

_DEGREE_RANK: Dict[Degrees, int] = {deg: i for i, deg in enumerate(TERTIAN_STACK_ORDER)}


def degree_rank(deg: Degrees) -> int:
    return _DEGREE_RANK.get(deg, 999)


def interval_rank(iv: Intervals) -> int:
    return degree_rank(iv.degree)


def order_by_responsibility(a: Intervals, b: Intervals) -> tuple[Intervals, Intervals]:
    """
    返回 (earlier, later)，其中 later 默认承担“解决责任”。
    """
    ra, rb = interval_rank(a), interval_rank(b)
    if ra < rb:
        return a, b
    if rb < ra:
        return b, a
    return (a, b) if a.semitones <= b.semitones else (b, a)


def is_aug_triad_pitchclass_set(semi_set: FrozenSet[int]) -> bool:
    if len(semi_set) != 3:
        return False
    mn = min(semi_set)
    norm = frozenset(((x - mn) % 12) for x in semi_set)
    return norm == frozenset({0, 4, 8})


def _always_step_either(_: Intervals) -> Resolution:
    return Resolution.STEP_EITHER


# 你确认 P4 不协和，因此保留 P4/A4/d5 等半音差规则。
EDGE_RULES: Tuple[EdgeRule, ...] = (
    EdgeRule(
        delta_semitones=1,
        kind="m2",
        priority=60,
        earlier_resolution=Resolution.NONE,
        later_resolution=Resolution.STEP_DOWN,
    ),
    EdgeRule(
        delta_semitones=2,
        kind="M2",
        priority=55,
        earlier_resolution=Resolution.NONE,
        later_resolution=Resolution.STEP_DOWN,
    ),
    EdgeRule(
        delta_semitones=5,
        kind="P4",
        priority=70,
        earlier_resolution=Resolution.NONE,
        later_resolution=Resolution.STEP_DOWN,
    ),
    EdgeRule(
        delta_semitones=6,
        kind="tritone",
        priority=100,
        earlier_resolution=Resolution.STEP_EITHER,
        later_resolution=Resolution.STEP_EITHER,
    ),
    EdgeRule(
        delta_semitones=10,
        kind="m7",
        priority=65,
        earlier_resolution=Resolution.NONE,
        later_resolution=Resolution.STEP_DOWN,
    ),
    EdgeRule(
        delta_semitones=11,
        kind="M7",
        priority=75,
        earlier_resolution=Resolution.NONE,
        later_resolution=Resolution.STEP_DOWN,
    ),
)

EDGE_RULE_BY_DELTA: Dict[int, EdgeRule] = {r.delta_semitones: r for r in EDGE_RULES}


SET_RULES: Tuple[SetRule, ...] = (
    SetRule(
        kind="aug_set",
        priority=90,
        min_moves=1,
        match=is_aug_triad_pitchclass_set,
        resolution_for_member=_always_step_either,
    ),
)


def iter_triads(items: Iterable[Intervals]) -> Iterable[Tuple[Intervals, Intervals, Intervals]]:
    lst = list(items)
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            for k in range(j + 1, len(lst)):
                yield lst[i], lst[j], lst[k]
