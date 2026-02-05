from dataclasses import dataclass
from typing import FrozenSet
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import VariantForm


@dataclass(frozen=True, slots=True)
class ChordConstraint:
    avoid_roots: FrozenSet[Degrees] = frozenset()
    avoid_variants: FrozenSet[VariantForm] = frozenset()
    must_include: FrozenSet[Degrees] = frozenset()
    forbid_include: FrozenSet[Degrees] = frozenset()
