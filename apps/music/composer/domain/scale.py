from typing import Iterable, Optional, Tuple, FrozenSet
from .base_note import BaseNote
from .color_shift import ColorShift
from .enums.core import Degrees, Intervals
from ._intern import InternedMeta, FrozenSlotsMixin


class Scale(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("tonic", "intervals", "note_list", "_note_set", "__weakref__")

    @classmethod
    def _cache_key(cls, tonic: BaseNote, intervals: Tuple[Intervals, ...]):
        return tonic, intervals

    def __init__(self, tonic: BaseNote, intervals: Tuple[Intervals, ...]):
        if not isinstance(intervals, tuple):
            raise TypeError("Scale intervals 必须为 tuple[Intervals, ...]（不可变）")
        if len(intervals) != 7:
            raise ValueError("Scale intervals 必须为长度 7（对应 I~VII）")
        if intervals[0] != Intervals.P1:
            raise ValueError("Scale intervals[0] 必须为 P1（保证 I 级为主音）")

        self.tonic = tonic
        self.intervals: Tuple[Intervals, ...] = intervals
        self.note_list = tuple(tonic + itv for itv in self.intervals)
        self._note_set = frozenset(self.note_list)
        self._freeze()

    def __getitem__(self, degree: Degrees) -> BaseNote:
        return self.note_list[degree.value - 1]

    def __len__(self) -> int:
        return 7

    def __iter__(self) -> Iterable[BaseNote]:
        return iter(self.note_list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scale):
            return NotImplemented
        return self.tonic == other.tonic and self.intervals == other.intervals

    def __hash__(self) -> int:
        return hash((self.tonic, self.intervals))

    def __contains__(self, base_note: BaseNote) -> bool:
        return self | base_note is not None

    def __or__(self, other: object) -> Optional[Degrees]:
        if not isinstance(other, BaseNote):
            return None
        for degree in Degrees:
            if self[degree] == other:
                return degree
        return None

    def __str__(self) -> str:
        return ", ".join(str(note) for note in self.note_list)

    def __sub__(self, other: object) -> ColorShift:
        if not isinstance(other, Scale):
            return NotImplemented
        diff = (other.tonic.offset - self.tonic.offset) % 12
        return ColorShift(self.intervals, diff, other.intervals)

    def __add__(self, other: object) -> "Scale":
        if not isinstance(other, ColorShift):
            return NotImplemented
        if other.src != self.intervals:
            raise ValueError("ColorShift.src 与当前 Scale.intervals 不匹配")
        new_offset = (self.tonic.offset + other.diff) % 12
        try:
            new_tonic = BaseNote.from_name_and_offset(self.tonic.note_name, new_offset)
        except ValueError as e:
            raise ValueError("ColorShift.diff 无法在当前 note_name 下表示") from e
        return Scale(new_tonic, other.dst)

    def pitch_class_set(self) -> FrozenSet[int]:
        return frozenset(n.offset for n in self.note_list)

    def respell(self, other: "Scale") -> bool:
        return isinstance(other, Scale) and self.pitch_class_set() == other.pitch_class_set()
