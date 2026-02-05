# Start chord rule
from ..constraints import Constraint, Violation
from .utils import chord_info_from_candidate, resolve_key
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import VariantForm


class StartChordRule(Constraint):
    def check(self, ctx, candidate):
        progression = getattr(ctx, "progression", [])
        if progression:
            return None
        key = resolve_key(ctx)
        if key is None:
            return None
        info = chord_info_from_candidate(ctx, candidate)
        if info is None:
            return None
        _, mode_id, chord_id = info
        mode = mode_id.resolve(key)
        ok = (
            mode.mode_type == key.main_mode_type
            and chord_id.variant == VariantForm.Base
            and chord_id.degree in {Degrees.I, Degrees.IV, Degrees.VI}
        )
        if ok:
            return None
        return Violation(code="start_chord", message="invalid start chord")
