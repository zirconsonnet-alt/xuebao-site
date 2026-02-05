import json
import sys
from pathlib import Path
from typing import Any


def _add_repo_root_to_syspath() -> None:
    p = Path(__file__).resolve()
    cur = p
    while cur.parent != cur and cur.name != "xuebao-site":
        cur = cur.parent
    if cur.name == "xuebao-site":
        sys.path.insert(0, str(cur))


def _to_jsonable(obj: Any) -> Any:
    try:
        from enum import Enum

        if isinstance(obj, Enum):
            return obj.name
    except Exception:
        pass
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(_to_jsonable(k)): _to_jsonable(v) for k, v in obj.items()}
    return str(obj)


def main() -> None:
    _add_repo_root_to_syspath()

    from apps.music.composer.analysis.api.analyze import analyze_hit  # noqa: E402
    from apps.music.composer.analysis.resolve.resolver import Resolver  # noqa: E402
    from apps.music.composer.domain.base_note import BaseNote  # noqa: E402
    from apps.music.composer.domain.chord import Chord  # noqa: E402
    from apps.music.composer.domain.enums.core import Degrees, Intervals, NoteNames  # noqa: E402
    from apps.music.composer.domain.enums.harmony import ModeAccess, Modes, VariantForm  # noqa: E402
    from apps.music.composer.domain.key import Key  # noqa: E402
    from apps.music.composer.domain.relations import ChordId, ModeId  # noqa: E402
    from apps.music.composer.domain.scale import Scale  # noqa: E402

    key = Key(BaseNote(NoteNames.C), Modes.Ionian)

    def run_case(label: str, chord) -> None:
        hits = Resolver().resolve(chord, key)
        print(f"\n== {label} ==")
        print(f"hits: {len(hits)}")
        if not hits:
            return
        analysis = analyze_hit(hits[0])
        if analysis is None:
            print("no analyzer for hit")
            return
        grouped = {g.value: d for g, d in analysis.view().as_grouped_dict().items()}
        print(json.dumps(_to_jsonable(grouped), ensure_ascii=False, indent=2))

    # C大调：G vs Gm 的属功能强度差异
    mode_c_ionian = ModeId(role=Degrees.I, access=ModeAccess.Relative).resolve(key)
    chord_g = ChordId(
        degree=Degrees.V,
        variant=VariantForm.Base,
        composition=frozenset({Degrees.I, Degrees.III, Degrees.V}),
    ).resolve(mode_c_ionian)
    run_case("C Key: G (major triad)", chord_g)

    # 构造 G 小三和弦：使用 G Aeolian 音阶（包含 Bb），取 I-III-V 组合得到 G-Bb-D
    g_aeolian = Scale(
        tonic=BaseNote(NoteNames.G),
        intervals=(Intervals.P1, Intervals.M2, Intervals.m3, Intervals.P4, Intervals.P5, Intervals.m6, Intervals.m7),
    )
    chord_gm = Chord(g_aeolian, composition=frozenset({Degrees.I, Degrees.III, Degrees.V}))
    run_case("C Key: Gm (minor triad)", chord_gm)

    # A自然小调：Emin vs Emaj 的属功能强度差异（应当 Emaj 更强）
    key_a_aeolian = Key(BaseNote(NoteNames.A), Modes.Aeolian)
    mode_a_aeolian = ModeId(role=Degrees.I, access=ModeAccess.Relative).resolve(key_a_aeolian)
    chord_emin = ChordId(
        degree=Degrees.V,
        variant=VariantForm.Base,
        composition=frozenset({Degrees.I, Degrees.III, Degrees.V}),
    ).resolve(mode_a_aeolian)
    hits = Resolver().resolve(chord_emin, key_a_aeolian)
    print("\n== A Aeolian Key: Emin (v) ==")
    print(f"hits: {len(hits)}")
    if hits:
        a = analyze_hit(hits[0])
        grouped = {g.value: d for g, d in a.view().as_grouped_dict().items()}
        print(json.dumps(_to_jsonable(grouped), ensure_ascii=False, indent=2))

    # 构造 E大三和弦：E harmonic minor 的 V（E-G#-B）
    e_maj = Scale(
        tonic=BaseNote(NoteNames.E),
        intervals=(Intervals.P1, Intervals.M2, Intervals.M3, Intervals.P4, Intervals.P5, Intervals.M6, Intervals.M7),
    )
    chord_emaj = Chord(e_maj, composition=frozenset({Degrees.I, Degrees.III, Degrees.V}))
    hits = Resolver().resolve(chord_emaj, key_a_aeolian)
    print("\n== A Aeolian Key: Emaj (V) ==")
    print(f"hits: {len(hits)}")
    if hits:
        a = analyze_hit(hits[0])
        grouped = {g.value: d for g, d in a.view().as_grouped_dict().items()}
        print(json.dumps(_to_jsonable(grouped), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
