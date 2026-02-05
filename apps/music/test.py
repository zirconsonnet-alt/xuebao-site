import sys
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


def _fmt_resolution(r: Resolution) -> str:
    return {
        Resolution.NONE: "无需解决",
        Resolution.STEP_UP: "上行级进解决",
        Resolution.STEP_DOWN: "下行级进解决",
        Resolution.STEP_EITHER: "级进解决(任意方向)",
    }[r]


def print_quality_dissonance(q: Quality) -> None:
    print(f"Quality: {q.name}")
    rels = q.dissonance_relations
    if not rels:
        print("  (无不协和关系)")
        return
    rels = sorted(rels, key=lambda r: (-r.priority, r.kind, sorted(iv.name for iv in r.notes)))
    for idx, rel in enumerate(rels, 1):
        notes = ", ".join(iv.name for iv in sorted(rel.notes, key=lambda x: (x.degree.value, x.semitones)))
        print(f"  [{idx}] kind={rel.kind}  priority={rel.priority}  notes={{ {notes} }}  min_moves={rel.min_moves}")
        rm = rel.resolution_map()
        for iv in sorted(rel.notes, key=lambda x: (x.degree.value, x.semitones)):
            print(f"       - {iv.name}: {_fmt_resolution(rm.get(iv, Resolution.NONE))}")


def main() -> int:
    samples = [
        Quality(base=Qualities.sus4),
        Quality(base=Qualities.maj7sus4),
        Quality(base=Qualities.aug),
        Quality(base=Qualities.maj, tensions=frozenset({Intervals.M2})),  # maj(add9)
        Quality(base=Qualities._7, tensions=frozenset({Intervals.P4})),  # 7(add11)
        Quality(base=Qualities.min, tensions=frozenset({Intervals.M6})),  # min(add13)
    ]
    for q in samples:
        print_quality_dissonance(q)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
