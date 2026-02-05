from dataclasses import dataclass
from typing import Optional, Union, Dict
from ._lookup import LookupEnum
from .core import Degrees
from .harmony import VariantForm


class DynamicType(LookupEnum):
    Strong = "strong"
    Weak = "weak"


@dataclass(frozen=True)
class DegreeVariant:
    degree: Degrees
    variant: Optional[VariantForm] = None


TargetPoint = DegreeVariant


class TurningPoints(LookupEnum):
    Descending_VI = DegreeVariant(Degrees.VI, VariantForm.Descending)
    Ascending_VI = DegreeVariant(Degrees.VI, VariantForm.Ascending)
    Descending_VII = DegreeVariant(Degrees.VII, VariantForm.Descending)
    Ascending_VII = DegreeVariant(Degrees.VII, VariantForm.Ascending)

    def next(self) -> DegreeVariant:
        rules: Dict[TurningPoints, DegreeVariant] = {
            TurningPoints.Descending_VII: DegreeVariant(Degrees.VI, variant=VariantForm.Descending),
            TurningPoints.Ascending_VI: DegreeVariant(Degrees.VII, variant=VariantForm.Ascending),
            TurningPoints.Descending_VI: DegreeVariant(Degrees.I, variant=None),
            TurningPoints.Ascending_VII: DegreeVariant(Degrees.V, variant=None),
        }
        return rules[self]


class States(LookupEnum):
    Consonant = "consonant"
    Dissonant = "dissonant"


class Voices(LookupEnum):
    Bass = "bass"
    Tenor = "tenor"
    Alto = "alto"
    Soprano = "soprano"


class LeadingType(LookupEnum):
    Step = "step"
    Jump = "jump"
    Suspend = "suspend"
    Transit = "transit"
