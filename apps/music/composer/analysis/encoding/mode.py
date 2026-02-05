# Encoding utilities for mode
from dataclasses import dataclass
from functools import cached_property
from typing import List, Tuple

from ..core.encoding import multi_hot
from ...domain.enums.harmony import Modes
from ...domain.mode import Mode
from ...domain.enums.harmony import VariantForm


@dataclass(frozen=True, slots=True)
class ModeEncodingVocab:
    semitone_order: Tuple[int, ...] = tuple(range(12))
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
        return len(self.semitone_order) + len(self.modes_order)


@dataclass(frozen=True, slots=True)
class ModeMetaVectorizer:
    vocab: ModeEncodingVocab = ModeEncodingVocab()

    @property
    def dim(self) -> int:
        return self.vocab.dim

    def vectorize(self, mode: Mode) -> List[float]:
        if not isinstance(mode, Mode):
            raise TypeError("vectorize requires Mode")
        base_profile = mode.spec.variants[VariantForm.Base]
        semitones = [iv.semitones for iv in base_profile]
        scale_vec = multi_hot(semitones, self.vocab.semitone_order)
        mode_vec = multi_hot([mode.mode_type], self.vocab.modes_order)
        return scale_vec + mode_vec


@dataclass(frozen=True, slots=True)
class ModeVectorizer:
    vocab: ModeEncodingVocab = ModeEncodingVocab()

    @cached_property
    def meta(self) -> ModeMetaVectorizer:
        return ModeMetaVectorizer(self.vocab)

    @property
    def dim(self) -> int:
        return self.meta.dim

    def vectorize(self, mode: Mode) -> List[float]:
        return self.meta.vectorize(mode)
