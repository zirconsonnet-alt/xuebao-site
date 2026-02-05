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


class DecisionImportTests(unittest.TestCase):
    def test_decision_package_imports_without_torch(self) -> None:
        # torch is an optional dependency; importing decision.* should not crash if torch isn't installed.
        import apps.music.composer.decision as _  # noqa: F401


if __name__ == "__main__":
    unittest.main()

