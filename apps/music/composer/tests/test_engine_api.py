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

from apps.music.composer.domain.enums.core import Degrees  # noqa: E402
from apps.music.composer.domain.relations import map_degree_to_target_root  # noqa: E402
from apps.music.composer.runtime.engine import generate_triplets  # noqa: E402
from apps.music.composer.runtime.engine.goals import CadenceSDTGoal, GoalSchedule  # noqa: E402


class EngineApiTests(unittest.TestCase):
    def test_generate_triplets_returns_length(self) -> None:
        triplets = generate_triplets(5, seed=0, beam_width=8, stage_budget=50, max_attempts=3)
        self.assertEqual(len(triplets), 5)

    def test_generate_triplets_with_cadence_sdt_goal(self) -> None:
        length = 3
        schedule = GoalSchedule(length=length, cadence_sdt=CadenceSDTGoal())
        triplets = generate_triplets(
            length,
            seed=0,
            beam_width=8,
            stage_budget=200,
            max_attempts=6,
            goal_schedule=schedule,
        )
        self.assertEqual(len(triplets), length)
        roots = [map_degree_to_target_root(mode_id, chord_id.degree) for _, mode_id, chord_id in triplets]
        self.assertIn(roots[-3], {Degrees.II, Degrees.IV})
        self.assertEqual(roots[-2], Degrees.V)
        self.assertEqual(roots[-1], Degrees.I)


if __name__ == "__main__":
    unittest.main()
