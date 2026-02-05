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

from apps.music.composer.domain.dissonance import EDGE_RULE_BY_DELTA, Resolution  # noqa: E402


class TritoneRuleTests(unittest.TestCase):
    def test_tritone_allows_both_sides_to_resolve(self) -> None:
        rule = EDGE_RULE_BY_DELTA[6]
        self.assertEqual(rule.kind, "tritone")
        self.assertEqual(rule.earlier_resolution, Resolution.STEP_EITHER)
        self.assertEqual(rule.later_resolution, Resolution.STEP_EITHER)
        self.assertEqual(rule.min_moves, 1)


if __name__ == "__main__":
    unittest.main()

