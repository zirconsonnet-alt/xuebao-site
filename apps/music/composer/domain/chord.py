from typing import AbstractSet, FrozenSet, Set, Optional
from .scale import Scale
from .quality import Quality
from .base_note import BaseNote
from .transition import Transition
from .enums.core import Degrees, Intervals
from .color_shift import ColorShift
from ._intern import InternedMeta, FrozenSlotsMixin


_DEFAULT_TRIAD: FrozenSet[Degrees] = frozenset({Degrees.I, Degrees.III, Degrees.V})


class Chord(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("scale", "_composition", "_base_notes", "_quality", "__weakref__")

    @classmethod
    def _cache_key(
        cls,
        scale: Scale,
        composition: AbstractSet[Degrees] | None = None,
    ):
        if composition is None:
            composition = _DEFAULT_TRIAD
        return scale, frozenset(composition)

    def __init__(
        self,
        scale: Scale,
        composition: AbstractSet[Degrees] | None = None,
    ):
        self.scale = scale
        if composition is None:
            composition = _DEFAULT_TRIAD
        self._set_composition(composition)

    def _set_composition(self, composition: AbstractSet[Degrees]) -> None:
        if not all(isinstance(d, Degrees) for d in composition):
            raise TypeError("Chord composition 必须为 Degrees 的集合（表示相对根音的级数差）")
        if Degrees.I not in composition:
            raise ValueError("Chord composition 必须包含 Degrees.I（表示根音）")
        if len(composition) < 2:
            raise ValueError("Chord composition 必须包含 大于等于 2 个级数")
        self._composition: FrozenSet[Degrees] = frozenset(composition)
        self._base_notes: FrozenSet[BaseNote] = frozenset(
            self.scale[rel] for rel in self._composition
        )
        root_offset = self.scale.tonic.offset
        interval_set: Set[Intervals] = set()
        for rel in self._composition:
            if rel == Degrees.I:
                continue
            semitone = (self.scale[rel].offset - root_offset) % 12
            interval_set.add(Intervals.get((rel, semitone)))
        self._quality = Quality.from_intervals(frozenset(interval_set))
        self._freeze()

    @property
    def composition(self) -> FrozenSet[Degrees]:
        return self._composition

    def with_composition(self, composition: AbstractSet[Degrees]) -> "Chord":
        return Chord(self.scale, composition)

    def __getitem__(self, item: Degrees) -> BaseNote:
        return self.scale[item]

    def __str__(self) -> str:
        return f"{self.scale.tonic}{self.quality.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Chord):
            return NotImplemented
        return self.scale == other.scale and self.composition == other.composition

    def __contains__(self, item: object) -> bool:
        if isinstance(item, BaseNote):
            return self | item is not None
        return False

    def __or__(self, other: object) -> Optional[Degrees]:
        if isinstance(other, BaseNote):
            degree = self.scale | other
            if degree is None:
                return None
            return degree if degree in self._composition else None
        if isinstance(other, Degrees):
            return other if other in self._composition else None
        return None

    def __iter__(self):
        return iter(self._base_notes)

    def __len__(self) -> int:
        return len(self._base_notes)

    @staticmethod
    def _composition_from_quality(quality: Quality) -> FrozenSet[Degrees]:
        degrees = {Degrees.I}
        for iv in quality.base.value:
            degrees.add(iv.degree)
        for iv in quality.tensions:
            degrees.add(iv.degree)
        for iv in quality.omits:
            degrees.discard(iv.degree)
        degrees.add(Degrees.I)
        return frozenset(degrees)

    def __sub__(self, other: "Chord") -> tuple[Transition, ColorShift]:
        transition = Transition(
            other.quality,
            (self.scale.tonic.offset - other.scale.tonic.offset) % 12,
            self.quality,
        )
        color_shift = other.scale - self.scale
        return transition, color_shift

    def __add__(self, other: object) -> "Chord":
        if (
            isinstance(other, tuple)
            and len(other) == 2
            and any(isinstance(x, Transition) for x in other)
            and any(isinstance(x, ColorShift) for x in other)
        ):
            transition = next(x for x in other if isinstance(x, Transition))
            color_shift = next(x for x in other if isinstance(x, ColorShift))
        else:
            return NotImplemented
        if transition.src != self.quality:
            raise ValueError("Transition.src 与当前 Chord.quality 不匹配")
        new_scale = self.scale + color_shift
        composition = self._composition_from_quality(transition.dst)
        return Chord(new_scale, composition)

    def __hash__(self) -> int:
        return hash((self.scale, self.composition))

    @property
    def base_notes(self) -> FrozenSet[BaseNote]:
        return self._base_notes

    @property
    def quality(self) -> Quality:
        return self._quality

    @property
    def pitch_classes(self) -> FrozenSet[int]:
        return frozenset(n.offset for n in self._base_notes)
