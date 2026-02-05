# Module for kinds
from enum import Enum, auto


class ResolveKind(Enum):
    ChordInMode = auto()
    ModeInKey = auto()
    ChordInKey = auto()


class AnalysisKind(Enum):
    ChordInMode = auto()
    ModeInKey = auto()
    Chord = auto()
    Mode = auto()
    Key = auto()
    ChordInKey = auto()
