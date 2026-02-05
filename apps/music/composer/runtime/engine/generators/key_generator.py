import random
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from ....domain.enums.core import NoteNames
from ....domain.enums.harmony import Modes
from ....domain.relations import KeyId
from ..constraints.key_constraint import KeyConstraint
from .enumeration import PrefixEnumerator, RelationSpec


def _as_frozenset(obj, default):
    if obj is None:
        return default
    return obj


def _build_spec(
    *,
    candidates: Optional[Sequence[KeyId]],
    domain: Optional[KeyConstraint],
) -> RelationSpec[KeyId]:
    # Preserve the historical default: when no domain/candidates are provided, use C Ionian only.
    if domain is None and candidates is None:

        def roots() -> Sequence[object]:
            return [NoteNames.C]

        def children(prefix: Tuple[object, ...]) -> Sequence[object]:
            return [Modes.Ionian]

        def forbidden(prefix: Tuple[object, ...], value: object) -> bool:
            return False

        def assemble(values: Tuple[object, ...]) -> KeyId:
            tonic, mode = values
            return KeyId(tonic=tonic, main_mode_type=mode)

        return RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)

    avoid_tonics = _as_frozenset(getattr(domain, "avoid_tonics", None), frozenset()) if domain else frozenset()
    avoid_modes = _as_frozenset(getattr(domain, "avoid_modes", None), frozenset()) if domain else frozenset()

    cand_map: Optional[Dict[NoteNames, List[Modes]]] = None
    if candidates is not None:
        cand_map = {}
        for kid in candidates:
            if kid.tonic in avoid_tonics or kid.main_mode_type in avoid_modes:
                continue
            cand_map.setdefault(kid.tonic, []).append(kid.main_mode_type)

    def roots() -> Sequence[object]:
        if cand_map is not None:
            return list(cand_map.keys())
        return [t for t in NoteNames if t not in avoid_tonics]

    def children(prefix: Tuple[object, ...]) -> Sequence[object]:
        # prefix == (tonic,)
        tonic = prefix[0]
        if not isinstance(tonic, NoteNames):
            return []
        if cand_map is not None:
            return cand_map.get(tonic, [])
        return [m for m in Modes if m not in avoid_modes]

    def forbidden(prefix: Tuple[object, ...], value: object) -> bool:
        if len(prefix) == 0:
            return isinstance(value, NoteNames) and value in avoid_tonics
        return isinstance(value, Modes) and value in avoid_modes

    def assemble(values: Tuple[object, ...]) -> KeyId:
        tonic, mode = values
        if not isinstance(tonic, NoteNames) or not isinstance(mode, Modes):
            raise TypeError("KeyId fields type mismatch")
        return KeyId(tonic=tonic, main_mode_type=mode)

    return RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)


class KeyGenerator:
    def __init__(
        self,
        candidates: Optional[List[KeyId]] = None,
        candidate_pool_size: int = 5,
        *,
        rng: Optional[random.Random] = None,
    ):
        self.candidates = candidates
        self.candidate_pool_size = candidate_pool_size
        self.rng = rng or random.Random()

    def propose(self, domain: Optional[KeyConstraint] = None) -> List[KeyId]:
        spec = _build_spec(candidates=self.candidates, domain=domain)
        enum = PrefixEnumerator(spec, self.rng)
        return list(enum.propose(self.candidate_pool_size))
