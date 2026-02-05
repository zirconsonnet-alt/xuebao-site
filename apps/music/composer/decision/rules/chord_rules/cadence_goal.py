# Cadence goal rule (hard, schedule-driven)
from __future__ import annotations

from ..constraints import Constraint, Violation
from ....domain.relations import ChordId, map_degree_to_target_root


class CadenceSDTGoalRule(Constraint):
    """
    Enforce a hard S-D-T cadence at the end of the sequence, driven by ctx.goal_schedule.

    This rule only checks absolute root degrees (in key's main-mode coordinate system):
    - S: {II, IV}
    - D: V
    - T: I

    It does not constrain chord quality, composition, or variant.
    """

    def check(self, ctx, candidate):
        schedule = getattr(ctx, "goal_schedule", None)
        if schedule is None:
            return None
        cadence = getattr(schedule, "cadence_sdt", None)
        length = getattr(schedule, "length", None)
        if cadence is None or not isinstance(length, int):
            return None
        if not isinstance(candidate, ChordId):
            return None

        mode_id = getattr(ctx, "current_mode_id", None)
        if mode_id is None:
            return None

        index = len(getattr(ctx, "progression", []) or [])
        allowed_roots_at = getattr(cadence, "allowed_roots_at", None)
        if not callable(allowed_roots_at):
            return None
        allowed = allowed_roots_at(index, length=length)
        if allowed is None:
            return None

        abs_root = map_degree_to_target_root(mode_id, candidate.degree)
        if abs_root in allowed:
            return None
        return Violation(code="goal_cadence_sdt", message=f"终止式目标未满足: step={index}, root={abs_root.name}")
