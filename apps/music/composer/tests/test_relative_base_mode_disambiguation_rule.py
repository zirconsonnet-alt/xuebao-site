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

from apps.music.composer.decision.rules.chord_rules import RelativeBaseModeDisambiguationRule  # noqa: E402
from apps.music.composer.domain.enums.core import Degrees, NoteNames  # noqa: E402
from apps.music.composer.domain.enums.harmony import ModeAccess, Modes, VariantForm  # noqa: E402
from apps.music.composer.domain.relations import ChordId, KeyId, ModeId  # noqa: E402
from apps.music.composer.runtime.engine import GenerationContext  # noqa: E402


class RelativeBaseModeDisambiguationRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rule = RelativeBaseModeDisambiguationRule()
        self.key_id = KeyId(tonic=NoteNames.C, main_mode_type=Modes.Ionian)

    def _ctx(self, mode_id: ModeId) -> GenerationContext:
        ctx = GenerationContext(rng=random.Random(0))
        ctx.current_key_id = self.key_id
        ctx.current_mode_id = mode_id
        return ctx

    def test_allows_main_mode_base_triad(self) -> None:
        ctx = self._ctx(ModeId(role=Degrees.I, access=ModeAccess.Relative))
        cand = ChordId(degree=Degrees.II, variant=VariantForm.Base, composition=frozenset({Degrees.I, Degrees.III, Degrees.V}))
        self.assertIsNone(self.rule.check(ctx, cand))

    def test_blocks_non_i_relative_base_without_characteristic(self) -> None:
        # D Dorian in key of C; Dm triad doesn't contain Dorian characteristic degree (VI) in mode coordinates.
        ctx = self._ctx(ModeId(role=Degrees.II, access=ModeAccess.Relative))
        cand = ChordId(degree=Degrees.I, variant=VariantForm.Base, composition=frozenset({Degrees.I, Degrees.III, Degrees.V}))
        self.assertIsNotNone(self.rule.check(ctx, cand))

    def test_allows_non_i_relative_base_with_characteristic(self) -> None:
        # D Dorian with Dm6 includes VI (characteristic) in mode coordinates.
        ctx = self._ctx(ModeId(role=Degrees.II, access=ModeAccess.Relative))
        cand = ChordId(
            degree=Degrees.I,
            variant=VariantForm.Base,
            composition=frozenset({Degrees.I, Degrees.III, Degrees.V, Degrees.VI}),
        )
        self.assertIsNone(self.rule.check(ctx, cand))

    def test_allows_non_i_relative_non_base_variant(self) -> None:
        ctx = self._ctx(ModeId(role=Degrees.II, access=ModeAccess.Relative))
        cand = ChordId(degree=Degrees.I, variant=VariantForm.Ascending, composition=frozenset({Degrees.I, Degrees.III, Degrees.V}))
        self.assertIsNone(self.rule.check(ctx, cand))


if __name__ == "__main__":
    unittest.main()

