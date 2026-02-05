from typing import Iterable, List, Optional, Sequence, TypeVar
from ..resolve.resolver import Resolver
from ..encoding.chord import ChordMetaVectorizer
from ..encoding.chord_in_mode import ChordInModeVectorizer
from ..encoding.mode import ModeMetaVectorizer
from ..encoding.mode_in_key import ModeInKeyVectorizer
from ..encoding.key import KeyMetaVectorizer, KeyIndexVectorizer
from ..core.hits.chord_in_mode import ChordInModeHit
from ..core.hits.mode_in_key import ModeInKeyHit
from ...domain.chord import Chord
from ...domain.key import Key
from ...domain.mode import Mode
from ...domain.enums.harmony import ModeAccess, VariantForm

T = TypeVar("T")

_RESOLVER = Resolver()
_CHORD_META_VECTORIZER = ChordMetaVectorizer()
_CHORD_IN_MODE_VECTORIZER = ChordInModeVectorizer()
_MODE_META_VECTORIZER = ModeMetaVectorizer()
_MODE_IN_KEY_VECTORIZER = ModeInKeyVectorizer()
_KEY_META_VECTORIZER = KeyMetaVectorizer()
_KEY_INDEX_VECTORIZER = KeyIndexVectorizer()


def _first_of_type(items: Iterable[T]) -> Optional[T]:
    for it in items:
        return it
    return None


def _pick_chord_in_mode_hit(
    hits: Iterable[ChordInModeHit],
    preferred_variant_order: Optional[Sequence[VariantForm]] = None,
) -> Optional[ChordInModeHit]:
    if preferred_variant_order is None:
        preferred_variant_order = (VariantForm.Base, VariantForm.Ascending, VariantForm.Descending)
    preferred = {v: i for i, v in enumerate(preferred_variant_order)}
    sorted_hits = sorted(
        hits,
        key=lambda h: (
            preferred.get(h.variant, 99),
            h.degree.value,
            tuple(sorted(h.composition, key=lambda d: d.value)),
        ),
    )
    return _first_of_type(sorted_hits)


def _pick_mode_in_key_hit(
    hits: Iterable[ModeInKeyHit],
    preferred_access_order: Optional[Sequence[ModeAccess]] = None,
) -> Optional[ModeInKeyHit]:
    if preferred_access_order is None:
        preferred_access_order = (ModeAccess.Substitute, ModeAccess.Relative, ModeAccess.SubV)
    access_rank = {v: i for i, v in enumerate(preferred_access_order)}

    def rank(hit: ModeInKeyHit) -> int:
        return access_rank.get(hit.access, 99)

    def role_rank(hit: ModeInKeyHit) -> int:
        return hit.role.value

    def tonic_rank(hit: ModeInKeyHit) -> int:
        try:
            return hit.mode.tonic.offset
        except Exception:
            return 99

    sorted_hits = sorted(hits, key=lambda h: (rank(h), role_rank(h), tonic_rank(h)))
    return _first_of_type(sorted_hits)


def vectorize_chord(
    chord: Chord,
    *,
    mode: Optional[Mode] = None,
    preferred_variant_order: Optional[Sequence[VariantForm]] = None,
) -> Sequence[float]:
    vec: List[float] = []
    vec.extend(_CHORD_META_VECTORIZER.vectorize(chord))

    chord_in_mode_hit: Optional[ChordInModeHit] = None
    if mode is not None:
        hits = _RESOLVER.resolve(chord, mode)
        chord_in_mode_hit = _pick_chord_in_mode_hit(
            (hit for hit in hits if isinstance(hit, ChordInModeHit)),
            preferred_variant_order=preferred_variant_order,
        )
        if chord_in_mode_hit is not None:
            vec.extend(_CHORD_IN_MODE_VECTORIZER.vectorize(chord_in_mode_hit))

    # evidence no longer contributes to features
    return vec


def vectorize_mode(
    mode: Mode,
    *,
    key: Optional[Key] = None,
    preferred_access_order: Optional[Sequence[ModeAccess]] = None,
) -> Sequence[float]:
    vec: List[float] = []
    vec.extend(_MODE_META_VECTORIZER.vectorize(mode))

    mode_hit: Optional[ModeInKeyHit] = None
    if key is not None:
        hits = _RESOLVER.resolve(mode, key)
        mode_hit = _pick_mode_in_key_hit(
            (hit for hit in hits if isinstance(hit, ModeInKeyHit)),
            preferred_access_order=preferred_access_order,
        )
        if mode_hit is not None:
            vec.extend(_MODE_IN_KEY_VECTORIZER.vectorize(mode_hit))
    return vec


def vectorize_key(key: Key) -> Sequence[float]:
    vec: List[float] = []
    vec.extend(_KEY_META_VECTORIZER.vectorize(key))
    vec.extend(_KEY_INDEX_VECTORIZER.vectorize(key))
    return vec
