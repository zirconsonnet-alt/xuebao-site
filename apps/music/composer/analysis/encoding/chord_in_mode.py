# Encoding utilities for chord in mode
from dataclasses import dataclass
from typing import List, Tuple
from ..core.encoding import multi_hot
from ..core.hits.chord_in_mode import ChordInModeHit
from ...domain.enums.core import Degrees
from ...domain.enums.harmony import VariantForm


@dataclass(frozen=True, slots=True)
class ChordInModeEncodingVocab:
    degrees_order: Tuple[Degrees, ...] = (
        Degrees.I,
        Degrees.II,
        Degrees.III,
        Degrees.IV,
        Degrees.V,
        Degrees.VI,
        Degrees.VII,
    )
    variant_order: Tuple[VariantForm, ...] = (
        VariantForm.Base,
        VariantForm.Ascending,
        VariantForm.Descending,
    )

    @property
    def dim(self) -> int:
        return len(self.variant_order) + len(self.degrees_order) + len(self.degrees_order)


@dataclass(frozen=True, slots=True)
class ChordInModeVectorizer:
    vocab: ChordInModeEncodingVocab = ChordInModeEncodingVocab()

    @property
    def dim(self) -> int:
        return self.vocab.dim

    def vectorize(self, hit: ChordInModeHit) -> List[float]:
        if not isinstance(hit, ChordInModeHit):
            raise TypeError("vectorize requires ChordInModeHit")
        variant_vec = multi_hot([hit.chord_id.variant], self.vocab.variant_order)
        degree_vec = multi_hot([hit.chord_id.degree], self.vocab.degrees_order)
        composition = hit.chord_id.composition or frozenset()
        composition_vec = multi_hot(composition, self.vocab.degrees_order)
        return variant_vec + degree_vec + composition_vec
