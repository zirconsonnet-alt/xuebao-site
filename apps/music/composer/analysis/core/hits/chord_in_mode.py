from dataclasses import dataclass
from typing import FrozenSet, Set
from ....domain.chord import Chord
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import VariantForm
from ....domain.mode import Mode
from ....domain.relations import ChordId
from ....domain.enums.runtime import TurningPoints, DegreeVariant
from ...core.hit import ResolveHit, format_degrees
from ...core.kinds import ResolveKind


@dataclass(frozen=True, slots=True)
class ChordInModeHit(ResolveHit):
    mode: Mode
    chord: Chord
    chord_id: ChordId

    @property
    def variant(self) -> VariantForm:
        return self.chord_id.variant

    @property
    def degree(self) -> Degrees:
        return self.chord_id.degree

    @property
    def composition(self) -> FrozenSet[Degrees]:
        return frozenset(self.chord_id.composition or frozenset())

    def chord_degrees_in_mode_scale(self) -> Set[Degrees]:
        return {self.degree + d for d in self.composition}

    def turning_points(self) -> Set[TurningPoints]:
        if self.variant == VariantForm.Base:
            return set()
        chord_degrees = self.chord_degrees_in_mode_scale()
        focus = chord_degrees & {Degrees.VI, Degrees.VII}
        tps = set()
        for d in focus:
            try:
                tps.add(TurningPoints(DegreeVariant(d, self.variant)))
            except ValueError:
                continue
        return tps

    def has_characteristic_degree(self) -> bool:
        chord_degrees = self.chord_degrees_in_mode_scale()
        return self.mode.spec.characteristic_degree in chord_degrees

    @property
    def kind(self) -> ResolveKind:
        return ResolveKind.ChordInMode

    def __str__(self) -> str:
        degs = format_degrees(frozenset(self.chord_id.composition or []))
        return (
            f"[Chord∈Mode] chord={self.chord} -> root={self.chord_id.degree.name}, degrees={degs} "
            f"in mode={self.mode}[{self.chord_id.variant.name}]"
        )
