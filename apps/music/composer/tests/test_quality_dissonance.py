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

from apps.music.composer.domain.enums.core import Intervals  # noqa: E402
from apps.music.composer.domain.enums.harmony import Qualities  # noqa: E402
from apps.music.composer.domain.quality import Quality, Resolution  # noqa: E402


class QualityDissonanceTests(unittest.TestCase):
    def test_sus4_only_4_resolves(self) -> None:
        q = Quality(base=Qualities.sus4)
        d = q.dissonance_dict
        key = frozenset({Intervals.P4, Intervals.P5})
        self.assertIn(key, d)
        self.assertEqual(d[key][Intervals.P4], Resolution.STEP_DOWN)  # later 负责
        self.assertEqual(d[key][Intervals.P5], Resolution.NONE)  # earlier 不负责
        rel = next(r for r in q.dissonance_relations if r.notes == key)
        self.assertEqual(rel.min_moves, 1)
        self.assertEqual(rel.kind, "m7")

    def test_aug_all_notes_resolvable(self) -> None:
        q = Quality(base=Qualities.aug)
        d = q.dissonance_dict
        key = frozenset({Intervals.P1, Intervals.M3, Intervals.A5})
        self.assertIn(key, d)
        self.assertEqual(d[key][Intervals.P1], Resolution.STEP_EITHER)
        self.assertEqual(d[key][Intervals.M3], Resolution.STEP_EITHER)
        self.assertEqual(d[key][Intervals.A5], Resolution.STEP_EITHER)
        rel = next(r for r in q.dissonance_relations if r.notes == key)
        self.assertEqual(rel.min_moves, 1)
        self.assertEqual(rel.kind, "aug_set")

    def test_tension_defaults_to_step_down(self) -> None:
        q = Quality(base=Qualities.maj, tensions=frozenset({Intervals.M2}))
        d = q.dissonance_dict
        key = frozenset({Intervals.P1, Intervals.M2})
        self.assertIn(key, d)
        self.assertEqual(d[key][Intervals.P1], Resolution.NONE)
        self.assertEqual(d[key][Intervals.M2], Resolution.STEP_DOWN)
        rel = next(r for r in q.dissonance_relations if r.notes == key)
        self.assertEqual(rel.min_moves, 1)
        self.assertEqual(rel.kind, "M2")


if __name__ == "__main__":
    unittest.main()
