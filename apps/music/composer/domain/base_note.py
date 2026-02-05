from .enums.core import NoteNames, Intervals
from ._intern import InternedMeta, FrozenSlotsMixin


class BaseNote(FrozenSlotsMixin, metaclass=InternedMeta):
    MAX_SHIFTS = 2
    __slots__ = ("note_name", "shifts", "offset", "__weakref__")

    @classmethod
    def _cache_key(cls, note_name: NoteNames, shifts: int = 0):
        return note_name, int(shifts)

    def __init__(self, note_name: NoteNames, shifts: int = 0):
        if abs(shifts) > self.MAX_SHIFTS:
            raise ValueError(f"升降号数量不能超过{self.MAX_SHIFTS}个")
        self.note_name = note_name
        self.shifts = int(shifts)
        self.offset = (note_name.value + self.shifts) % 12
        self._freeze()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseNote):
            return NotImplemented
        return self.note_name == other.note_name and self.shifts == other.shifts

    def __hash__(self) -> int:
        return hash((self.note_name, self.shifts))

    def __str__(self) -> str:
        if self.shifts > 0:
            return f"{self.note_name.name}{'#' * self.shifts}"
        if self.shifts < 0:
            return f"{self.note_name.name}{'b' * (-self.shifts)}"
        return self.note_name.name

    def __sub__(self, interval: Intervals) -> "BaseNote":
        note_name = self.note_name - interval.value[0]
        offset = (self.offset - interval.value[1]) % 12
        return BaseNote.from_name_and_offset(note_name, offset)

    def __add__(self, interval: Intervals) -> "BaseNote":
        note_name = self.note_name + interval.value[0]
        offset = (self.offset + interval.value[1]) % 12
        return BaseNote.from_name_and_offset(note_name, offset)

    def __or__(self, other: object) -> Intervals:
        if not isinstance(other, BaseNote):
            return NotImplemented
        key = (other.note_name | self.note_name, (other.offset - self.offset) % 12)
        return Intervals.get(key)

    def respell(self, other: "BaseNote") -> bool:
        return isinstance(other, BaseNote) and self.offset == other.offset

    @staticmethod
    def from_name_and_offset(note_name: NoteNames, offset: int) -> "BaseNote":
        if not 0 <= offset < 12:
            raise ValueError("相对音高必须在0到11之间")
        delta = (offset - note_name.value) % 12
        delta = delta - 12 if delta > 6 else delta
        if abs(delta) > BaseNote.MAX_SHIFTS:
            raise ValueError(
                f"无法在升降号数量≤{BaseNote.MAX_SHIFTS}的约束下表示: "
                f"{note_name.name} -> offset {offset} (需要 shifts={delta})"
            )
        return BaseNote(note_name, delta)
