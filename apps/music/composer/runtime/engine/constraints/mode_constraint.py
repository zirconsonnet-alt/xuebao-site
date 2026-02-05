# Domain constraints for mode candidate generation
from dataclasses import dataclass
from typing import FrozenSet
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import Modes, ModeAccess


@dataclass(frozen=True, slots=True)
class ModeConstraint:
    avoid_roles: FrozenSet[Degrees] = frozenset()
    avoid_modes: FrozenSet[Modes] = frozenset()
    avoid_access: FrozenSet[ModeAccess] = frozenset()
