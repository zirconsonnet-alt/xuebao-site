# Module for resolver
from typing import List, Tuple, Union
from ...domain.key import Key
from ...domain.mode import Mode
from ...domain.chord import Chord
from ...domain.enums.core import Degrees
from ...domain.enums.harmony import ModeAccess, VariantForm
from ...domain.relations import ChordId, ModeId
from ..core.hits.mode_in_key import ModeInKeyHit
from ..core.hits.chord_in_mode import ChordInModeHit
from ..core.hits.chord_in_key import ChordInKeyHit

AnyResolveHit = Union[
    ChordInModeHit,
    ModeInKeyHit,
    ChordInKeyHit,
]


class Resolver:
    def resolve(self, a, b) -> List[AnyResolveHit]:
        hits: List[AnyResolveHit] = []
        swapped = self._should_swap(a, b)
        if swapped:
            a, b = b, a
        if isinstance(a, Chord) and isinstance(b, Mode):
            hits.extend(self._resolve_chord_in_mode(chord=a, mode=b))
            return hits
        if isinstance(a, Mode) and isinstance(b, Key):
            hits.extend(self._resolve_mode_in_key(mode=a, key=b))
            return hits
        if isinstance(a, Chord) and isinstance(b, Key):
            hits.extend(self._resolve_chord_in_key(chord=a, key=b))
            return hits
        return hits

    @staticmethod
    def _should_swap(a, b) -> bool:
        supported = (
            (Chord, Mode),
            (Mode, Key),
            (Chord, Key),
        )

        def is_supported(x, y) -> bool:
            return any(isinstance(x, A) and isinstance(y, B) for (A, B) in supported)
        return (not is_supported(a, b)) and is_supported(b, a)

    @staticmethod
    def _mode_variants(mode: Mode) -> Tuple[VariantForm, ...]:
        return tuple(mode.spec.variants.keys())

    def _resolve_chord_in_mode(self, chord: Chord, mode: Mode) -> List[AnyResolveHit]:
        hits: List[AnyResolveHit] = []
        variants = self._mode_variants(mode)
        chord_notes = chord.base_notes
        chord_root = chord.scale.tonic
        for variant in variants:
            base = mode.scale(variant)
            root_deg = base | chord_root
            if root_deg is None:
                continue
            ok = True
            for n in chord_notes:
                if (base | n) is None:
                    ok = False
                    break
            if not ok:
                continue
            hits.append(
                ChordInModeHit(
                    mode=mode,
                    chord=chord,
                    chord_id=ChordId(
                        degree=root_deg,
                        variant=variant,
                        composition=frozenset(chord.composition),
                    ),
                )
            )
        return hits

    def _resolve_chord_in_key(self, chord: Chord, key: Key) -> List[AnyResolveHit]:
        hits: List[AnyResolveHit] = []

        def extend(mode: Mode, mode_id: ModeId) -> None:
            for h in self._resolve_chord_in_mode(chord=chord, mode=mode):
                if not isinstance(h, ChordInModeHit):
                    continue
                hits.append(
                    ChordInKeyHit(
                        key=key,
                        mode=mode,
                        chord=chord,
                        mode_id=mode_id,
                        chord_id=h.chord_id,
                    )
                )

        for mt, m in key.modes_by_type.items():
            extend(m, ModeId(role=mt, access=ModeAccess.Substitute))

        for deg, m in key.modes_by_degree.items():
            extend(m, ModeId(role=deg, access=ModeAccess.Relative))

        for deg in Degrees:
            try:
                m = key[(deg, ModeAccess.SubV)]
            except (KeyError, ValueError):
                continue
            extend(m, ModeId(role=deg, access=ModeAccess.SubV))

        return hits

    @staticmethod
    def _resolve_mode_in_key(mode: Mode, key: Key) -> List[AnyResolveHit]:
        hits: List[AnyResolveHit] = []
        for mt, m in key.modes_by_type.items():
            if m == mode:
                hits.append(
                    ModeInKeyHit(
                        key=key,
                        mode=mode,
                        access=ModeAccess.Substitute,
                        role=mt,
                    )
                )
        for deg, m in key.modes_by_degree.items():
            if m == mode:
                hits.append(
                    ModeInKeyHit(
                        key=key,
                        mode=mode,
                        access=ModeAccess.Relative,
                        role=deg,
                    )
                )
        for deg in Degrees:
            try:
                sub_mode = key[(deg, ModeAccess.SubV)]
            except (KeyError, ValueError):
                continue
            if sub_mode == mode:
                hits.append(
                    ModeInKeyHit(
                        key=key,
                        mode=mode,
                        access=ModeAccess.SubV,
                        role=deg,
                    )
                )
        return hits

