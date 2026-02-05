# Resolution rule for chord progression
from ..constraints import Constraint, Violation
from .utils import chord_info_from_candidate, resolve_key
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import Qualities


class ResolutionRule(Constraint):
    def check(self, ctx, candidate):
        progression = getattr(ctx, "progression", [])
        if not progression:
            return None
        key = resolve_key(ctx)
        if key is None:
            return None
        cur_info = chord_info_from_candidate(ctx, candidate)
        if cur_info is None:
            return None
        ex_info = progression[-1]
        _, ex_mode_id, ex_chord_id = ex_info
        _, cur_mode_id, cur_chord_id = cur_info
        ex_mode = ex_mode_id.resolve(key)
        cur_mode = cur_mode_id.resolve(key)
        ex_chord = ex_chord_id.resolve(ex_mode)
        cur_chord = cur_chord_id.resolve(cur_mode)

        def directed_delta(target: int, s: int) -> int:
            return ((target - s + 6) % 12) - 6

        resolution_map = self._resolution_map(ex_chord)
        for degree, allowed in resolution_map.items():
            src = ex_chord[degree].offset
            ok = any(directed_delta(bn.offset, src) in allowed for bn in cur_chord.base_notes)
            if not ok:
                return Violation(code="resolution", message="resolution rule violated")
        return None

    @staticmethod
    def _resolution_map(chord):
        base = chord.quality.base
        if base == Qualities.dim:
            return {Degrees.V: {-1, -2}}
        if base == Qualities.aug:
            return {Degrees.V: {1}}
        return {}
