# Encoding utilities for key
from dataclasses import dataclass
from functools import cached_property
from typing import List, Tuple
from ..core.encoding import multi_hot
from ...domain.enums.harmony import Modes
from ...domain.key import Key
from ...domain.enums.harmony import VariantForm


@dataclass(frozen=True, slots=True)
class KeyEncodingVocab:
    modes_order: Tuple[Modes, ...] = (
        Modes.Ionian,
        Modes.Dorian,
        Modes.Phrygian,
        Modes.Lydian,
        Modes.Mixolydian,
        Modes.Aeolian,
        Modes.Locrian,
    )
    semitone_order: Tuple[int, ...] = tuple(range(12))
    @property
    def meta_dim(self) -> int:
        return len(self.semitone_order)

    @property
    def index_dim(self) -> int:
        return len(self.modes_order) + len(self.semitone_order)

    @property
    def total_dim(self) -> int:
        return self.meta_dim + self.index_dim


@dataclass(frozen=True, slots=True)
class KeyMetaVectorizer:
    vocab: KeyEncodingVocab = KeyEncodingVocab()

    @property
    def dim(self) -> int:
        return self.vocab.meta_dim

    @staticmethod
    def vectorize_with_vocab(key: Key, vocab: KeyEncodingVocab) -> List[float]:
        if not isinstance(key, Key):
            raise TypeError("vectorize requires Key")
        main_mode = key[key.main_mode_type]
        base_profile = main_mode.spec.variants[VariantForm.Base]
        intervals = [iv.semitones for iv in base_profile]
        scale_vec = multi_hot(intervals, vocab.semitone_order)
        return scale_vec

    def vectorize(self, key: Key) -> List[float]:
        return self.vectorize_with_vocab(key, self.vocab)


@dataclass(frozen=True, slots=True)
class KeyIndexVectorizer:
    vocab: KeyEncodingVocab = KeyEncodingVocab()

    @property
    def dim(self) -> int:
        return self.vocab.index_dim

    @staticmethod
    def vectorize_with_vocab(key: Key, vocab: KeyEncodingVocab) -> List[float]:
        if not isinstance(key, Key):
            raise TypeError("vectorize requires Key")
        mode_vec = multi_hot([key.main_mode_type], vocab.modes_order)
        tonic_vec = multi_hot([key.tonic.offset], vocab.semitone_order)
        return mode_vec + tonic_vec

    def vectorize(self, key: Key) -> List[float]:
        return self.vectorize_with_vocab(key, self.vocab)


@dataclass(frozen=True, slots=True)
class KeyVectorizer:
    vocab: KeyEncodingVocab = KeyEncodingVocab()

    @cached_property
    def meta(self) -> KeyMetaVectorizer:
        return KeyMetaVectorizer(self.vocab)

    @cached_property
    def index(self) -> KeyIndexVectorizer:
        return KeyIndexVectorizer(self.vocab)

    @property
    def dim(self) -> int:
        return self.vocab.total_dim

    def vectorize(self, key: Key) -> List[float]:
        return self.meta.vectorize(key) + self.index.vectorize(key)
