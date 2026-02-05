import random
from itertools import combinations
from typing import FrozenSet, Iterator, List, Optional, Sequence, Tuple, cast
from ....domain import Chord, Mode
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import VariantForm
from ....domain.relations import ChordId
from ..constraints.chord_constraint import ChordConstraint
from .enumeration import PrefixEnumerator, RelationSpec


class ChordSpace:
    def build(
        self,
        mode: Mode,
        domain: Optional[ChordConstraint] = None,
    ) -> RelationSpec[ChordId]:
        if domain is None:
            domain = ChordConstraint()
        variants: List[VariantForm] = [v for v in list(mode.spec.variants.keys()) if v not in domain.avoid_variants]
        roots: List[Degrees] = [d for d in list(Degrees) if d not in domain.avoid_roots]
        feasible_roots: List[Degrees] = [r for r in roots if self._is_root_feasible(r, domain)]
        must_abs = domain.must_include
        forbid_abs = domain.forbid_include

        def roots_fn() -> Sequence[object]:
            return feasible_roots

        def children(prefix: Tuple[object, ...]) -> Sequence[object]:
            if len(prefix) == 1:
                root = prefix[0]
                if not isinstance(root, Degrees):
                    return []
                # Variants are closed under degree derivation (variant-first semantics).
                return variants
            if len(prefix) == 2:
                root, variant = prefix
                if not isinstance(root, Degrees) or not isinstance(variant, VariantForm):
                    return []
                try:
                    scale = mode.scale_of(root, variant)
                except ValueError:
                    return []

                comps = self._valid_compositions_for_root(root, must_abs, forbid_abs)
                valid: List[FrozenSet[Degrees]] = []
                for comp in comps:
                    try:
                        Chord(scale, comp)
                    except ValueError:
                        continue
                    valid.append(comp)
                return valid
            return []

        def forbidden(prefix: Tuple[object, ...], value: object) -> bool:
            if len(prefix) == 0:
                return isinstance(value, Degrees) and value in domain.avoid_roots
            if len(prefix) == 1:
                return isinstance(value, VariantForm) and value in domain.avoid_variants
            return False

        def assemble(values: Tuple[object, ...]) -> ChordId:
            root, variant, comp = values
            if not isinstance(root, Degrees) or not isinstance(variant, VariantForm) or not isinstance(comp, frozenset):
                raise TypeError("ChordId fields type mismatch")
            return ChordId(degree=root, variant=variant, composition=comp)
        return RelationSpec(depth=3, roots=roots_fn, children=children, forbidden=forbidden, assemble=assemble)

    @staticmethod
    def _is_root_feasible(
        root: Degrees,
        domain: ChordConstraint,
    ) -> bool:
        if domain.must_include & domain.forbid_include:
            return False
        must_rel = {deg - root for deg in domain.must_include}
        forbid_rel = {deg - root for deg in domain.forbid_include}
        if Degrees.I in forbid_rel:
            return False
        if must_rel & forbid_rel:
            return False
        fixed = set(must_rel)
        fixed.add(Degrees.I)
        pool = [d for d in Degrees if d != Degrees.I and d not in forbid_rel and d not in fixed]
        need_min = 2 - len(fixed) if len(fixed) < 2 else 0
        return need_min <= len(pool)

    @staticmethod
    def _valid_compositions_for_root(
        root: Degrees,
        must_abs: FrozenSet[Degrees],
        forbid_abs: FrozenSet[Degrees],
    ) -> List[FrozenSet[Degrees]]:
        if must_abs & forbid_abs:
            return []
        must_rel = {deg - root for deg in must_abs}
        forbid_rel = {deg - root for deg in forbid_abs}
        if Degrees.I in forbid_rel:
            return []
        if must_rel & forbid_rel:
            return []
        fixed = set(must_rel)
        fixed.add(Degrees.I)
        pool = [d for d in Degrees if d != Degrees.I and d not in forbid_rel and d not in fixed]
        need_min = 2 - len(fixed) if len(fixed) < 2 else 0
        if need_min > len(pool):
            return []
        results: List[FrozenSet[Degrees]] = []
        for extra_size in range(0, len(pool) + 1):
            if len(fixed) + extra_size < 2:
                continue
            for extra in combinations(pool, extra_size):
                results.append(frozenset([*fixed, *extra]))
        return results


class ChordGenerator:
    def __init__(self, candidate_pool_size: int = 300, *, rng: Optional[random.Random] = None):
        self.candidate_pool_size = candidate_pool_size
        self.rng = rng or random.Random()

    def propose(
        self,
        mode: Mode,
        domain: Optional[ChordConstraint] = None,
    ) -> Iterator:
        spec = ChordSpace().build(mode, domain=domain)
        return PrefixEnumerator(spec, self.rng).propose(self.candidate_pool_size)
