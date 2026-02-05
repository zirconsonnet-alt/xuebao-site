from dataclasses import dataclass
from typing import List, Tuple
from ..core.encoding import multi_hot
from ...domain.chord import Chord


SEMITONE_ORDER: Tuple[int, ...] = tuple(range(12))


@dataclass(frozen=True, slots=True)
class ChordEncodingVocab:
    semitone_order: Tuple[int, ...] = SEMITONE_ORDER

    @property
    def meta_dim(self) -> int:
        return len(self.semitone_order)


@dataclass(frozen=True, slots=True)
class ChordMetaVectorizer:
    vocab: ChordEncodingVocab = ChordEncodingVocab()

    @property
    def dim(self) -> int:
        return self.vocab.meta_dim

    def vectorize(self, chord: Chord) -> List[float]:
        if not isinstance(chord, Chord):
            raise TypeError("vectorize requires Chord")
        root_offset = chord.scale.tonic.offset
        semitones = {
            (chord.scale[deg].offset - root_offset) % 12 for deg in chord.composition
        }
        return multi_hot(semitones, self.vocab.semitone_order)
