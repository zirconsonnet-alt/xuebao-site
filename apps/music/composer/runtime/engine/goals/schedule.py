from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, FrozenSet, Optional

from ....domain.enums.core import Degrees


@dataclass(frozen=True, slots=True)
class CadenceSDTGoal:
    """
    Hard cadence goal: last three chords must be S-D-T by absolute root degrees.

    - S: root in {II, IV}
    - D: root == V
    - T: root == I

    "Absolute" means degrees are in the key's main-mode coordinate system.
    """

    s_roots: FrozenSet[Degrees] = frozenset({Degrees.II, Degrees.IV})
    d_root: Degrees = Degrees.V
    t_root: Degrees = Degrees.I

    def allowed_roots_at(self, index: int, *, length: int) -> Optional[AbstractSet[Degrees]]:
        if index == length - 3:
            return self.s_roots
        if index == length - 2:
            return frozenset({self.d_root})
        if index == length - 1:
            return frozenset({self.t_root})
        return None

    def goalset_id(self) -> str:
        s = ",".join(sorted(d.name for d in self.s_roots))
        return f"cadence_sdt:S={s};D={self.d_root.name};T={self.t_root.name}"


@dataclass(frozen=True, slots=True)
class GoalSchedule:
    length: int
    cadence_sdt: Optional[CadenceSDTGoal] = None

    @property
    def goalset_id(self) -> str:
        parts = [f"len={self.length}"]
        if self.cadence_sdt is not None:
            parts.append(self.cadence_sdt.goalset_id())
        return "|".join(parts)
