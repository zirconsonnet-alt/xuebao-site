# Module for note
from ..domain import BaseNote


class Note:
    __slots__ = ("base_note", "octave", "height")

    def __init__(self, base_note: BaseNote, octave: int):
        if not 0 <= octave <= 9:
            raise ValueError("请确保音符处在一个合理的八度（0~9）。")
        self.base_note = base_note
        self.octave = octave
        self.height = 12 * octave + base_note.offset

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Note):
            return NotImplemented
        return self.height == other.height

    def __hash__(self) -> int:
        return hash(self.height)

    def __str__(self) -> str:
        return f"{self.base_note}{self.octave}"
