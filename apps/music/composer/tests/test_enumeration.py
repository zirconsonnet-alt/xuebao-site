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

from apps.music.composer.runtime.engine.generators.enumeration import PrefixEnumerator, RelationSpec  # noqa: E402


class EnumerationTests(unittest.TestCase):
    def test_reproducible_sequence_same_seed(self) -> None:
        def mk(rng_seed: int):
            rng = random.Random(rng_seed)

            def roots():
                return [0, 1, 2]

            def children(prefix):
                if len(prefix) == 1:
                    return [10, 11]
                if len(prefix) == 2:
                    return [100, 101]
                return []

            def forbidden(prefix, value) -> bool:
                return False

            def assemble(values):
                return tuple(values)

            spec = RelationSpec(depth=3, roots=roots, children=children, forbidden=forbidden, assemble=assemble)
            return list(PrefixEnumerator(spec, rng).propose(20))

        a = mk(123)
        b = mk(123)
        self.assertEqual(a, b)

    def test_different_seed_changes_order(self) -> None:
        def mk(rng_seed: int):
            rng = random.Random(rng_seed)

            def roots():
                return list(range(10))

            def children(prefix):
                if len(prefix) == 1:
                    return [0, 1, 2]
                return []

            def forbidden(prefix, value) -> bool:
                return False

            def assemble(values):
                return tuple(values)

            spec = RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)
            return list(PrefixEnumerator(spec, rng).propose(20))

        a = mk(1)
        b = mk(2)
        self.assertNotEqual(a, b)

    def test_lazy_children_called_only_as_needed(self) -> None:
        calls = {"children": 0}
        rng = random.Random(0)

        def roots():
            return list(range(100))

        def children(prefix):
            calls["children"] += 1
            # Always one child; should only need to call this once for limit=1.
            return [0]

        def forbidden(prefix, value) -> bool:
            return False

        def assemble(values):
            return tuple(values)

        spec = RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)
        out = list(PrefixEnumerator(spec, rng, window=1).propose(1))
        self.assertEqual(len(out), 1)
        self.assertEqual(calls["children"], 1)

    def test_empty_branch_does_not_early_stop(self) -> None:
        visited = {"empty_root": False}
        rng = random.Random(1)  # chosen so that root 0 is visited first in LazyShuffler([0,1,2], seed=1)

        def roots():
            return [0, 1, 2]

        def children(prefix):
            if len(prefix) == 1:
                if prefix[0] == 0:
                    visited["empty_root"] = True
                    return []
                return [10]
            if len(prefix) == 2:
                return [100]
            return []

        def forbidden(prefix, value) -> bool:
            return False

        def assemble(values):
            return tuple(values)

        spec = RelationSpec(depth=3, roots=roots, children=children, forbidden=forbidden, assemble=assemble)
        out = list(PrefixEnumerator(spec, rng, window=3).propose(1))
        self.assertEqual(len(out), 1)
        self.assertNotEqual(out[0][0], 0)
        self.assertTrue(visited["empty_root"])

    def test_forbidden_is_applied(self) -> None:
        rng = random.Random(0)

        def roots():
            return [0]

        def children(prefix):
            if len(prefix) == 1:
                return [0, 1, 2]
            return []

        def forbidden(prefix, value) -> bool:
            # Forbid value==1 at B layer.
            return len(prefix) == 1 and value == 1

        def assemble(values):
            return tuple(values)

        spec = RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)
        out = list(PrefixEnumerator(spec, rng).propose(10))
        self.assertTrue(all(t[1] != 1 for t in out))

    def test_limit_is_respected(self) -> None:
        rng = random.Random(0)

        def roots():
            return list(range(10))

        def children(prefix):
            if len(prefix) == 1:
                return list(range(10))
            return []

        def forbidden(prefix, value) -> bool:
            return False

        def assemble(values):
            return tuple(values)

        spec = RelationSpec(depth=2, roots=roots, children=children, forbidden=forbidden, assemble=assemble)
        out = list(PrefixEnumerator(spec, rng).propose(3))
        self.assertEqual(len(out), 3)


if __name__ == "__main__":
    unittest.main()
