from typing import Dict, FrozenSet, List, Optional, Tuple
from .enums.harmony import Qualities
from .enums.core import Intervals
from .dissonance import (
    DissonanceRelation,
    Resolution,
    SET_RULES,
    EDGE_RULE_BY_DELTA,
    interval_rank,
    order_by_responsibility,
    iter_triads,
)
from ._intern import InternedMeta, FrozenSlotsMixin


class Quality(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("base", "tensions", "omits", "__weakref__")

    @classmethod
    def _cache_key(
        cls,
        base: Qualities,
        tensions: FrozenSet[Intervals] = frozenset(),
        omits: FrozenSet[Intervals] = frozenset(),
    ):
        return base, frozenset(tensions), frozenset(omits)

    def __init__(
        self,
        base: Qualities,
        tensions: FrozenSet[Intervals] = frozenset(),
        omits: FrozenSet[Intervals] = frozenset(),
    ):
        self.base = base
        self.tensions = frozenset(tensions)
        self.omits = frozenset(omits)
        self._freeze()

    @staticmethod
    def _interval_sort_key(iv: Intervals) -> tuple[int, int]:
        deg, semi = iv.value
        return deg.value, semi

    @staticmethod
    def _omit_token(iv: Intervals) -> str:
        deg, _ = iv.value
        if deg.value == 3:
            return "no3"
        if deg.value == 5:
            return "no5"
        if deg.value == 7:
            return "no7"
        if deg.value == 2:
            return "no9"
        if deg.value == 4:
            return "no11"
        return ""

    @property
    def name(self) -> str:
        s = self.base.name
        if self.tensions:
            ts = sorted(self.tensions, key=self._interval_sort_key)
            s += "(" + ",".join(iv.name for iv in ts) + ")"
        if self.omits:
            os = sorted(self.omits, key=self._interval_sort_key)
            tokens = [self._omit_token(iv) for iv in os]
            tokens = [t for t in tokens if t]
            if tokens:
                s += "/" + ",".join(tokens)
        return s

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quality):
            return NotImplemented
        return (
            self.base == other.base
            and self.tensions == other.tensions
            and self.omits == other.omits
        )

    def __hash__(self) -> int:
        return hash((self.base, self.tensions, self.omits))

    @property
    def dissonance_relations(self) -> List[DissonanceRelation]:
        present = frozenset((self.base.value - self.omits) | self.tensions)
        notes = frozenset({Intervals.P1, *present})
        rel_map: Dict[FrozenSet[Intervals], DissonanceRelation] = {}
        note_list = sorted(notes, key=lambda x: (interval_rank(x), x.semitones))
        for i in range(len(note_list)):
            for j in range(i + 1, len(note_list)):
                a = note_list[i]
                b = note_list[j]
                earlier, later = order_by_responsibility(a, b)
                delta = (later.semitones - earlier.semitones) % 12
                rule = EDGE_RULE_BY_DELTA.get(delta)
                if rule is None:
                    continue
                key = frozenset({earlier, later})
                if key in rel_map:
                    continue
                rel_map[key] = DissonanceRelation(
                    notes=key,
                    kind=rule.kind,
                    priority=rule.priority,
                    min_moves=rule.min_moves,
                    resolution=((earlier, rule.earlier_resolution), (later, rule.later_resolution)),
                )
        for a, b, c in iter_triads(note_list):
            semi_set = frozenset({a.semitones, b.semitones, c.semitones})
            for rule in SET_RULES:
                if not rule.match(semi_set):
                    continue
                key = frozenset({a, b, c})
                if key in rel_map:
                    continue
                rel_map[key] = DissonanceRelation(
                    notes=key,
                    kind=rule.kind,
                    priority=rule.priority,
                    min_moves=rule.min_moves,
                    resolution=tuple(
                        (iv, rule.resolution_for_member(iv))
                        for iv in sorted(key, key=lambda x: (interval_rank(x), x.semitones))
                    ),
                )
        return list(rel_map.values())

    @property
    def dissonance_dict(self) -> Dict[FrozenSet[Intervals], Dict[Intervals, Resolution]]:
        return {rel.notes: rel.resolution_map() for rel in self.dissonance_relations}

    @classmethod
    def from_intervals(cls, s: FrozenSet[Intervals]) -> "Quality":
        if not s:
            raise ValueError("Quality.from_intervals: 输入 interval 集合为空，无法推断 base quality")

        def is_allowed_tension(iv: Intervals) -> bool:
            deg, _ = iv.value
            return deg.value in (2, 4, 6)

        def is_allowed_omit(iv: Intervals) -> bool:
            deg, _ = iv.value
            return deg.value not in (1,)
        candidates: List[Tuple[Tuple[int, int, int], Qualities, FrozenSet[Intervals], FrozenSet[Intervals]]] = []
        for q in Qualities.__members__.values():
            base_set: FrozenSet[Intervals] = q.value
            missing = frozenset(base_set - s)
            extra = frozenset(s - base_set)
            if len(missing) > 1:
                continue
            if any(not is_allowed_omit(iv) for iv in missing):
                continue
            if any(not is_allowed_tension(iv) for iv in extra):
                continue
            if len(missing) == 0 and len(extra) == 0:
                score = (0, 0, 0)
            elif len(missing) == 1 and len(extra) == 0:
                score = (1, 0, 0)
            elif len(missing) == 0 and len(extra) >= 1:
                score = (2, 0, len(extra))
            elif len(missing) == 1 and len(extra) >= 1:
                score = (3, 0, len(extra))
            else:
                continue
            candidates.append((score, q, missing, extra))
        if not candidates:
            raise ValueError(f"Quality.from_intervals: 无法从 {sorted(iv.name for iv in s)} 推断出任何 Qualities")
        candidates.sort(key=lambda x: x[0])
        _, best_q, best_missing, best_extra = candidates[0]
        return cls(base=best_q, tensions=frozenset(best_extra), omits=frozenset(best_missing))

    @classmethod
    def try_from_intervals(cls, s: FrozenSet[Intervals]) -> Optional["Quality"]:
        try:
            return cls.from_intervals(s)
        except ValueError:
            return None
