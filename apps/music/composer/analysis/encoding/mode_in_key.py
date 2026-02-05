# Encoding utilities for mode in key
from dataclasses import dataclass
from typing import List, Tuple

from ..core.encoding import multi_hot
from ..core.hits.mode_in_key import ModeInKeyHit
from ...domain.enums.core import Degrees
from ...domain.enums.harmony import ModeAccess, Modes


@dataclass(frozen=True, slots=True)
class ModeInKeyEncodingVocab:
    degrees_order: Tuple[Degrees, ...] = (
        Degrees.I,
        Degrees.II,
        Degrees.III,
        Degrees.IV,
        Degrees.V,
        Degrees.VI,
        Degrees.VII,
    )
    modes_order: Tuple[Modes, ...] = (
        Modes.Ionian,
        Modes.Dorian,
        Modes.Phrygian,
        Modes.Lydian,
        Modes.Mixolydian,
        Modes.Aeolian,
        Modes.Locrian,
    )

    @property
    def dim(self) -> int:
        return 3 + len(self.modes_order) + len(self.degrees_order)


@dataclass(frozen=True, slots=True)
class ModeInKeyVectorizer:
    vocab: ModeInKeyEncodingVocab = ModeInKeyEncodingVocab()

    @property
    def dim(self) -> int:
        return self.vocab.dim

    def vectorize(self, hit: ModeInKeyHit) -> List[float]:
        if not isinstance(hit, ModeInKeyHit):
            raise TypeError("vectorize requires ModeInKeyHit")
        is_substitute = hit.access == ModeAccess.Substitute
        is_relative = hit.access == ModeAccess.Relative
        is_subv = hit.access == ModeAccess.SubV
        if is_substitute:
            if not isinstance(hit.role, Modes):
                raise TypeError("ModeInKeyHit.role must be Modes when access=Substitute")
        else:
            if not isinstance(hit.role, Degrees):
                raise TypeError("ModeInKeyHit.role must be Degrees when access!=Substitute")
        mode_vec = (
            multi_hot([hit.role], self.vocab.modes_order)
            if is_substitute
            else [0.0] * len(self.vocab.modes_order)
        )
        degree_vec = (
            multi_hot([hit.role], self.vocab.degrees_order)
            if not is_substitute
            else [0.0] * len(self.vocab.degrees_order)
        )
        return [1.0 if is_substitute else 0.0, 1.0 if is_relative else 0.0, 1.0 if is_subv else 0.0] + mode_vec + degree_vec
