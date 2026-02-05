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

from apps.music.composer.domain.enums.core import NoteNames  # noqa: E402
from apps.music.composer.domain.enums.harmony import Modes  # noqa: E402
from apps.music.composer.domain.relations import KeyId  # noqa: E402
from apps.music.composer.runtime.engine.generators.chord_generator import ChordGenerator  # noqa: E402


class ChordGeneratorVariantTests(unittest.TestCase):
    def test_chord_candidates_are_resolvable_under_variant_modes(self) -> None:
        key = KeyId(tonic=NoteNames.C, main_mode_type=Modes.Ionian).resolve()
        # Dorian 具有 Ascending/Descending 变体；历史上会生成 (degree, Ascending) 导致派生模式不支持而崩溃。
        mode = key[Modes.Dorian]
        gen = ChordGenerator(candidate_pool_size=300)
        count = 0
        for chord_id in gen.propose(mode):
            chord_id.resolve(mode)  # should not raise
            count += 1
            if count >= 100:
                break
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()

