import random
from typing import Iterator, List, Optional, Sequence, Tuple

from ....domain import Key, Mode
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import ModeAccess, Modes, VariantForm
from ....domain.relations import ModeId
from ....library import get_all_color_shifts
from ..constraints.mode_constraint import ModeConstraint
from .enumeration import PrefixEnumerator, RelationSpec


def _as_frozenset(obj, default):
    if obj is None:
        return default
    return obj


def _as_bool(obj, default: bool) -> bool:
    if obj is None:
        return default
    return bool(obj)


class ModeSpace:
    def __init__(self, *, include_subv: bool = False):
        self.include_subv = include_subv

    def build(
        self,
        key: Key,
        domain: Optional[ModeConstraint] = None,
        *,
        prev_mode: Optional[Mode] = None,
    ) -> RelationSpec[ModeId]:
        if domain is None:
            avoid_roles = frozenset()
            avoid_modes = frozenset()
            avoid_access = frozenset()
            allow_roles = frozenset()
            allow_modes = frozenset()
            include_subv = self.include_subv
        else:
            avoid_roles = _as_frozenset(getattr(domain, "avoid_roles", None), frozenset())
            avoid_modes = _as_frozenset(getattr(domain, "avoid_modes", None), frozenset())
            avoid_access = _as_frozenset(getattr(domain, "avoid_access", None), frozenset())
            allow_roles = _as_frozenset(getattr(domain, "allow_roles", None), frozenset())
            allow_modes = _as_frozenset(getattr(domain, "allow_modes", None), frozenset())
            include_subv = _as_bool(getattr(domain, "include_subv", None), self.include_subv) or self.include_subv

        rel_degs: List[Degrees] = [d for d in Degrees if d not in avoid_roles]
        sub_modes: List[Modes] = [m for m in Modes if m not in avoid_modes]
        subv_degs: List[Degrees] = [d for d in Degrees if d not in avoid_roles] if include_subv else []

        if allow_roles:
            rel_degs = [d for d in rel_degs if d in allow_roles]
            subv_degs = [d for d in subv_degs if d in allow_roles]
        if allow_modes:
            sub_modes = [m for m in sub_modes if m in allow_modes]

        allowed_shifts = get_all_color_shifts()

        def roots() -> Sequence[object]:
            # A layer: access
            items: List[ModeAccess] = []
            if ModeAccess.Relative not in avoid_access and rel_degs:
                items.append(ModeAccess.Relative)
            if ModeAccess.Substitute not in avoid_access and sub_modes:
                items.append(ModeAccess.Substitute)
            if include_subv and ModeAccess.SubV not in avoid_access and subv_degs:
                items.append(ModeAccess.SubV)
            return items

        def children(prefix: Tuple[object, ...]) -> Sequence[object]:
            # prefix == (access,)
            access = prefix[0]
            if access == ModeAccess.Relative:
                return rel_degs
            if access == ModeAccess.Substitute:
                return sub_modes
            if access == ModeAccess.SubV:
                return subv_degs
            return []

        def forbidden(prefix: Tuple[object, ...], value: object) -> bool:
            if len(prefix) == 0:
                return isinstance(value, ModeAccess) and value in avoid_access

            access = prefix[0]
            # B layer: role
            if access == ModeAccess.Relative and isinstance(value, Degrees) and value in avoid_roles:
                return True
            if access == ModeAccess.Substitute and isinstance(value, Modes) and value in avoid_modes:
                return True
            if access == ModeAccess.SubV and isinstance(value, Degrees) and value in avoid_roles:
                return True

            if prev_mode is None:
                return False

            # Additional constraint: color shift compatibility against prev_mode.
            if access == ModeAccess.Relative and isinstance(value, Degrees):
                mode = key[value]
            elif access == ModeAccess.Substitute and isinstance(value, Modes):
                mode = key[value]
            elif access == ModeAccess.SubV and isinstance(value, Degrees):
                mode = key[(value, ModeAccess.SubV)]
            else:
                return True
            shift = prev_mode.scale(VariantForm.Base) - mode.scale(VariantForm.Base)
            return shift not in allowed_shifts

        def assemble(values: Tuple[object, ...]) -> ModeId:
            access, role = values
            if not isinstance(access, ModeAccess):
                raise TypeError("ModeId.access type mismatch")
            return ModeId(role=role, access=access)

        return RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)


class ModeGenerator:
    def __init__(
        self,
        include_subv: bool = False,
        candidate_pool_size: int = 20,
        *,
        rng: Optional[random.Random] = None,
    ):
        self.include_subv = include_subv
        self.candidate_pool_size = candidate_pool_size
        self.rng = rng or random.Random()

    def propose(
        self,
        key: Key,
        domain: Optional[ModeConstraint] = None,
        *,
        prev_mode: Optional[Mode] = None,
    ) -> Iterator:
        spec = ModeSpace(include_subv=self.include_subv).build(key, domain=domain, prev_mode=prev_mode)
        enum = PrefixEnumerator(spec, self.rng)
        return enum.propose(self.candidate_pool_size)
