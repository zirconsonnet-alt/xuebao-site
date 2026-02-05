# Root progression rules
import itertools

from ..constraints import Constraint, Violation
from ....domain.enums.core import Degrees
from ....domain.relations import map_degree_to_target_root, ChordId


class RootNoRepeatRule(Constraint):
    def check(self, ctx, candidate):
        progression = getattr(ctx, "progression", [])
        roots = [map_degree_to_target_root(m, c.degree) for _, m, c in progression]
        if isinstance(candidate, ChordId):
            current_mode = getattr(ctx, "current_mode_id", None)
            if current_mode is not None:
                roots.append(map_degree_to_target_root(current_mode, candidate.degree))
        if len(roots) < 2:
            return None
        if any(roots[i] == roots[i + 1] for i in range(len(roots) - 1)):
            return Violation(code="root_repeat", message="adjacent roots repeat")
        return None


class RootPatternRule(Constraint):
    def check(self, ctx, candidate):
        progression = getattr(ctx, "progression", [])
        roots = [map_degree_to_target_root(m, c.degree) for _, m, c in progression]
        if isinstance(candidate, ChordId):
            current_mode = getattr(ctx, "current_mode_id", None)
            if current_mode is not None:
                roots.append(map_degree_to_target_root(current_mode, candidate.degree))
        if len(roots) <= 1:
            return None
        if len(roots) >= 4:
            recent = roots[-4:]
            triples = list(itertools.combinations(recent, 3))
            if any(t for t in triples if t[2] - t[1] == t[1] - t[0]):
                return None
            if roots[-1] - roots[-2] == roots[-3] - roots[-4]:
                return None
            return Violation(code="root_pattern", message="root pattern rejected")
        return None


class RootCadencePositionRule(Constraint):
    def check(self, ctx, candidate):
        progression = getattr(ctx, "progression", [])
        roots = [map_degree_to_target_root(m, c.degree) for _, m, c in progression]
        if isinstance(candidate, ChordId):
            current_mode = getattr(ctx, "current_mode_id", None)
            if current_mode is not None:
                roots.append(map_degree_to_target_root(current_mode, candidate.degree))
        if len(roots) == 0:
            return None
        if len(roots) % 4 == 0:
            if roots[-3] - roots[-2] in {Degrees.VII, Degrees.III, Degrees.V}:
                return None
            if (
                roots[-4] - roots[-3] in {Degrees.VII, Degrees.III, Degrees.V}
                and roots[-2] - roots[-1] in {Degrees.VII, Degrees.III, Degrees.V}
            ):
                return None
            return Violation(code="root_cadence", message="cadence position rejected")
        return None
