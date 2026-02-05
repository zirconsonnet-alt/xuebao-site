import sys
import unittest
from pathlib import Path


def _add_repo_root_to_syspath() -> None:
    p = Path(__file__).resolve()
    cur = p
    while cur.parent != cur and cur.name != "xuebao-site":
        cur = cur.parent
    if cur.name == "xuebao-site":
        sys.path.insert(0, str(cur))


_add_repo_root_to_syspath()

from apps.music.composer.decision.rules.chord_rules import CadenceSDTGoalRule  # noqa: E402
from apps.music.composer.domain.enums.core import Degrees, NoteNames  # noqa: E402
from apps.music.composer.domain.enums.harmony import ModeAccess, Modes, VariantForm  # noqa: E402
from apps.music.composer.domain.relations import ChordId, KeyId, ModeId  # noqa: E402
from apps.music.composer.runtime.engine import GenerationContext  # noqa: E402
from apps.music.composer.runtime.engine.goals import (  # noqa: E402
    CadenceSDTGoal,
    GoalSchedule,
    ReachabilityMemo,
    can_reach_cadence_sdt,
)


class GoalCadenceSDTTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schedule = GoalSchedule(length=3, cadence_sdt=CadenceSDTGoal())
        self.key_id = KeyId(tonic=NoteNames.C, main_mode_type=Modes.Ionian)
        self.mode_id = ModeId(role=Degrees.I, access=ModeAccess.Relative)

    def test_reachability_detects_adjacent_repeat_block(self) -> None:
        memo = ReachabilityMemo()
        self.assertTrue(
            can_reach_cadence_sdt(
                self.schedule,
                next_index=0,
                prev_root=None,
                last_root=None,
                memo=memo,
            )
        )
        # At index=1, the cadence requires V; if last_root is already V, adjacent repeat makes it unreachable.
        self.assertFalse(
            can_reach_cadence_sdt(
                self.schedule,
                next_index=1,
                prev_root=Degrees.II,
                last_root=Degrees.V,
                memo=memo,
            )
        )

    def test_cadence_rule_enforces_last_three_roots(self) -> None:
        rule = CadenceSDTGoalRule()
        ctx = GenerationContext(goal_schedule=self.schedule)
        ctx.current_key_id = self.key_id
        ctx.current_mode_id = self.mode_id

        # step 0 must be S: II or IV
        self.assertIsNone(rule.check(ctx, ChordId(degree=Degrees.II, variant=VariantForm.Base)))
        self.assertIsNotNone(rule.check(ctx, ChordId(degree=Degrees.V, variant=VariantForm.Base)))

        # commit step 0
        ctx.progression.append((self.key_id, self.mode_id, ChordId(degree=Degrees.II, variant=VariantForm.Base)))

        # step 1 must be D: V
        self.assertIsNone(rule.check(ctx, ChordId(degree=Degrees.V, variant=VariantForm.Base)))
        self.assertIsNotNone(rule.check(ctx, ChordId(degree=Degrees.I, variant=VariantForm.Base)))

        # commit step 1
        ctx.progression.append((self.key_id, self.mode_id, ChordId(degree=Degrees.V, variant=VariantForm.Base)))

        # step 2 must be T: I
        self.assertIsNone(rule.check(ctx, ChordId(degree=Degrees.I, variant=VariantForm.Base)))
        self.assertIsNotNone(rule.check(ctx, ChordId(degree=Degrees.IV, variant=VariantForm.Base)))


if __name__ == "__main__":
    unittest.main()

