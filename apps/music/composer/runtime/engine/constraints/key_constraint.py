from dataclasses import dataclass
from typing import FrozenSet
from ....domain.enums.core import NoteNames
from ....domain.enums.harmony import Modes


@dataclass(frozen=True, slots=True)
class KeyConstraint:
    avoid_tonics: FrozenSet[NoteNames] = frozenset()
    avoid_modes: FrozenSet[Modes] = frozenset()
