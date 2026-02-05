# Turning point rule for chord progression
from ..constraints import Constraint, Violation
from .utils import chord_info_from_candidate, resolve_key
from ....domain.enums.core import Degrees
from ....domain.enums.runtime import TurningPoints, DegreeVariant
from ....domain.enums.harmony import VariantForm


class TurningPointRule(Constraint):
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
        ex_mode = ex_mode_id.resolve(key)
        ex_degree = ex_chord_id.degree
        ex_variant = ex_chord_id.variant
        if ex_variant == VariantForm.Base:
            return None
        ex_chord = ex_chord_id.resolve(ex_mode)
        chord_degrees = {ex_degree + d for d in ex_chord.composition}
        focus = chord_degrees & {Degrees.VI, Degrees.VII}
        if not focus:
            return None
        target_degrees = set()
        for d in focus:
            try:
                tp = TurningPoints(DegreeVariant(d, ex_variant))
            except ValueError:
                continue
            target = tp.next()
            target_degrees.add(target.degree)
        if not target_degrees:
            return None
        _, cur_mode_id, cur_chord_id = cur_info
        cur_mode = cur_mode_id.resolve(key)
        cur_chord = cur_chord_id.resolve(cur_mode)
        cur_notes = set(cur_chord.base_notes)
        scale = ex_mode.scale(ex_variant)
        ok = all(scale[deg] in cur_notes for deg in target_degrees)
        if ok:
            return None
        return Violation(code="turning_point", message="turning point not resolved")
