import sys
from pathlib import Path
import argparse


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--stage-budget", type=int, default=200)
    parser.add_argument("--max-attempts", type=int, default=6)
    args = parser.parse_args()

    length = args.length
    seed = args.seed
    schedule = GoalSchedule(length=length, cadence_sdt=CadenceSDTGoal())

    triplets = generate_triplets(
        length,
        seed=seed,
        beam_width=args.beam_width,
        stage_budget=args.stage_budget,
        max_attempts=args.max_attempts,
        goal_schedule=schedule,
    )

    print(f"length={length} seed={seed}")
    print("Triplets:")
    for i, (key_id, mode_id, chord_id) in enumerate(triplets):
        abs_root = map_degree_to_target_root(mode_id, chord_id.degree)
        print(
            f"{i:02d}  key={key_id.tonic.name}-{key_id.main_mode_type.name:<9}"
            f"  mode=({mode_id.access.name},{getattr(mode_id.role, 'name', mode_id.role)})"
            f"  chord=({chord_id.degree.name},{chord_id.variant.name})"
            f"  abs_root={abs_root.name}"
        )

    roots = [map_degree_to_target_root(m, c.degree) for _, m, c in triplets]
    print("Abs roots:", " ".join(r.name for r in roots))
    print(
        "Cadence check:",
        roots[-3].name,
        "->",
        roots[-2].name,
        "->",
        roots[-1].name,
        "(expected II/IV -> V -> I)",
    )
    ok = roots[-3] in {Degrees.II, Degrees.IV} and roots[-2] == Degrees.V and roots[-1] == Degrees.I
    print("OK" if ok else "FAIL")


if __name__ == "__main__":
    main()
