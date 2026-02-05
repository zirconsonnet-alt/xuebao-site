import random
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

from apps.music.composer.decision.rules.mode_rules import ModeTransitionRule  # noqa: E402
from apps.music.composer.domain.enums.core import Degrees, NoteNames  # noqa: E402
from apps.music.composer.domain.enums.harmony import ModeAccess, Modes, VariantForm  # noqa: E402
from apps.music.composer.domain.relations import ChordId, KeyId, ModeId  # noqa: E402
from apps.music.composer.runtime.engine import GenerationContext  # noqa: E402


class ModeTransitionRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rule = ModeTransitionRule()
        self.key_id = KeyId(tonic=NoteNames.C, main_mode_type=Modes.Ionian)

    def _ctx_with_prev(self, prev: ModeId) -> GenerationContext:
        ctx = GenerationContext(rng=random.Random(0))
        ctx.current_key_id = self.key_id
        # chord_id is irrelevant for the rule check, but progression expects a triple.
        ctx.progression.append((self.key_id, prev, ChordId(degree=Degrees.I, variant=VariantForm.Base)))
        return ctx

    def test_main_to_relative_allowed(self) -> None:
        prev = ModeId(role=Degrees.I, access=ModeAccess.Relative)  # MAIN
        ctx = self._ctx_with_prev(prev)
        cand = ModeId(role=Degrees.II, access=ModeAccess.Relative)
        self.assertIsNone(self.rule.check(ctx, cand))

    def test_main_to_substitute_allowed(self) -> None:
        prev = ModeId(role=Degrees.I, access=ModeAccess.Relative)  # MAIN
        ctx = self._ctx_with_prev(prev)
        cand = ModeId(role=Modes.Dorian, access=ModeAccess.Substitute)
        self.assertIsNone(self.rule.check(ctx, cand))

    def test_relative_to_substitute_forbidden(self) -> None:
        prev = ModeId(role=Degrees.II, access=ModeAccess.Relative)
        ctx = self._ctx_with_prev(prev)
        cand = ModeId(role=Modes.Dorian, access=ModeAccess.Substitute)
        self.assertIsNotNone(self.rule.check(ctx, cand))

    def test_subv_only_with_same_degree_relative(self) -> None:
        prev = ModeId(role=Degrees.III, access=ModeAccess.SubV)
        ctx = self._ctx_with_prev(prev)
        ok = ModeId(role=Degrees.III, access=ModeAccess.Relative)
        bad = ModeId(role=Degrees.IV, access=ModeAccess.Relative)
        self.assertIsNone(self.rule.check(ctx, ok))
        self.assertIsNotNone(self.rule.check(ctx, bad))


if __name__ == "__main__":
    unittest.main()
