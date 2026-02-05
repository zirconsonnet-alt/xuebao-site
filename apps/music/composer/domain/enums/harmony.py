from enum import auto
from .core import Intervals
from ._lookup import LookupEnum


class Qualities(LookupEnum):
    maj = frozenset({Intervals.M3, Intervals.P5})
    min = frozenset({Intervals.m3, Intervals.P5})
    sus2 = frozenset({Intervals.M2, Intervals.P5})
    sus4 = frozenset({Intervals.P4, Intervals.P5})
    maj7sus2 = frozenset({Intervals.M2, Intervals.P5, Intervals.M7})
    min7sus2 = frozenset({Intervals.M2, Intervals.P5, Intervals.m7})
    maj7sus4 = frozenset({Intervals.P4, Intervals.P5, Intervals.M7})
    min7sus4 = frozenset({Intervals.P4, Intervals.P5, Intervals.m7})
    dim = frozenset({Intervals.m3, Intervals.d5})
    aug = frozenset({Intervals.M3, Intervals.A5})
    _5 = frozenset({Intervals.P5})
    maj7 = frozenset({Intervals.M3, Intervals.P5, Intervals.M7})
    _7 = frozenset({Intervals.M3, Intervals.P5, Intervals.m7})
    min7 = frozenset({Intervals.m3, Intervals.P5, Intervals.m7})
    mM7 = frozenset({Intervals.m3, Intervals.P5, Intervals.M7})
    dim7 = frozenset({Intervals.m3, Intervals.d5, Intervals.d7})
    min7b5 = frozenset({Intervals.m3, Intervals.d5, Intervals.m7})
    aug7 = frozenset({Intervals.M3, Intervals.A5, Intervals.M7})
    _7p = frozenset({Intervals.M3, Intervals.A5, Intervals.m7})
    maj9 = frozenset({Intervals.M3, Intervals.P5, Intervals.M7, Intervals.M2})
    maj11 = frozenset({Intervals.M3, Intervals.P5, Intervals.M7, Intervals.M2, Intervals.P4})
    maj13 = frozenset({Intervals.M3, Intervals.P5, Intervals.M7, Intervals.M2, Intervals.P4, Intervals.M6})
    min9 = frozenset({Intervals.m3, Intervals.P5, Intervals.m7, Intervals.M2})
    min11 = frozenset({Intervals.m3, Intervals.P5, Intervals.m7, Intervals.M2, Intervals.P4})
    min13 = frozenset({Intervals.m3, Intervals.P5, Intervals.m7, Intervals.M2, Intervals.P4, Intervals.M6})
    _9 = frozenset({Intervals.M3, Intervals.P5, Intervals.m7, Intervals.M2})
    _11 = frozenset({Intervals.M3, Intervals.P5, Intervals.m7, Intervals.M2, Intervals.P4})
    _13 = frozenset({Intervals.M3, Intervals.P5, Intervals.m7, Intervals.M2, Intervals.P4, Intervals.M6})


class Modes(LookupEnum):
    Ionian = 1
    Dorian = 2
    Phrygian = 3
    Lydian = 4
    Mixolydian = 5
    Aeolian = 6
    Locrian = 7


class VariantForm(LookupEnum):
    Base = auto()
    Ascending = auto()
    Descending = auto()


class Tonality(LookupEnum):
    maj = auto()
    min = auto()


class ChromaticType(LookupEnum):
    Base = auto()
    Degree = auto()
    Mode = auto()


class Functions(LookupEnum):
    Tonic = auto()
    Dominant = auto()
    Subdominant = auto()
    Characteristic = auto()


class ModeAccess(LookupEnum):
    Relative = auto()
    Substitute = auto()
    SubV = auto()
