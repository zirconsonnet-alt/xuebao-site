# Mode transition rules
from ..constraints import Constraint, Violation
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import ModeAccess
from ....domain.relations import KeyId, ModeId


class ModeTransitionRule(Constraint):
    """
    互转规则（按 access 类别约束）：
    - MAIN <-> REL 允许
    - MAIN <-> SUB 允许
    - REL <-> SUB 禁止
    - SUBV 只能与同级 REL 互转（同 degree）
    """

    def check(self, ctx, candidate):
        key_id = getattr(ctx, "current_key_id", None)
        if not isinstance(key_id, KeyId):
            return None

        if not isinstance(candidate, ModeId):
            return None

        progression = getattr(ctx, "progression", None) or []
        if not progression:
            return None
        prev_mode_id = progression[-1][1] if len(progression[-1]) >= 2 else None
        if not isinstance(prev_mode_id, ModeId):
            return None

        prev_cat = self._category(key_id, prev_mode_id)
        cand_cat = self._category(key_id, candidate)

        if prev_cat == "SUBV" or cand_cat == "SUBV":
            if prev_cat == "SUBV" and cand_cat == "REL" and self._same_degree(prev_mode_id, candidate):
                return None
            if prev_cat == "REL" and cand_cat == "SUBV" and self._same_degree(prev_mode_id, candidate):
                return None
            return Violation(code="mode_transition", message="subv 只能与同级关系调互转")

        if (prev_cat, cand_cat) in {("REL", "SUB"), ("SUB", "REL")}:
            return Violation(code="mode_transition", message="关系调与替换调不能直接互转")

        return None

    @staticmethod
    def _is_main(key_id: KeyId, mode_id: ModeId) -> bool:
        # main mode can be represented as:
        # - Relative degree I
        # - Substitute of key.main_mode_type
        if mode_id.access == ModeAccess.Relative and mode_id.role == Degrees.I:
            return True
        if mode_id.access == ModeAccess.Substitute and mode_id.role == key_id.main_mode_type:
            return True
        return False

    @classmethod
    def _category(cls, key_id: KeyId, mode_id: ModeId) -> str:
        if cls._is_main(key_id, mode_id):
            return "MAIN"
        if mode_id.access == ModeAccess.Relative:
            return "REL"
        if mode_id.access == ModeAccess.Substitute:
            return "SUB"
        if mode_id.access == ModeAccess.SubV:
            return "SUBV"
        return "OTHER"

    @staticmethod
    def _same_degree(a: ModeId, b: ModeId) -> bool:
        return isinstance(a.role, Degrees) and isinstance(b.role, Degrees) and a.role == b.role

