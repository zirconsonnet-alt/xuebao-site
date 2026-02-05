# Function flow rule for chord progression
from ..constraints import Constraint, Violation
from .utils import chord_info_from_candidate, resolve_key
from ....domain.enums.harmony import Functions


class FunctionFlowRule(Constraint):
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
        forbidden = {(Functions.Dominant, Functions.Subdominant)}
        ex_func1 = self._get_functions_for_degree(ex_chord, ex_mode)
        ex_func2 = self._get_functions_for_degree(cur_chord, ex_mode)
        cur_func1 = self._get_functions_for_degree(ex_chord, cur_mode)
        cur_func2 = self._get_functions_for_degree(cur_chord, cur_mode)
        ok = (
            not any((f1, f2) in forbidden for f1 in ex_func1 for f2 in ex_func2)
            and not any((f1, f2) in forbidden for f1 in cur_func1 for f2 in cur_func2)
        )
        if ok:
            return None
        return Violation(code="function_flow", message="function flow forbidden")

    @staticmethod
    def _get_functions_for_degree(chord, mode):
        result = set()
        tonic_off = mode.tonic.offset
        if any((bn.offset - tonic_off) % 12 == 0 for bn in chord.base_notes):
            result.add(Functions.Tonic)
        if any((bn.offset - tonic_off) % 12 == 5 for bn in chord.base_notes):
            result.add(Functions.Subdominant)
        if any((bn.offset - tonic_off) % 12 == 11 for bn in chord.base_notes):
            result.add(Functions.Dominant)
        return result
