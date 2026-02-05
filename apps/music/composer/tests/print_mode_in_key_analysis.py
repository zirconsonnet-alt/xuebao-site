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
    from apps.music.composer.domain.enums.core import Degrees, NoteNames  # noqa: E402
    from apps.music.composer.domain.enums.harmony import ModeAccess, Modes  # noqa: E402
    from apps.music.composer.domain.key import Key  # noqa: E402
    from apps.music.composer.domain.relations import ModeId  # noqa: E402

    key = Key(BaseNote(NoteNames.C), Modes.Ionian)
    mode = ModeId(role=Degrees.II, access=ModeAccess.Relative).resolve(key)  # D Dorian
    hits = Resolver().resolve(mode, key)
    print(f"hits: {len(hits)}")
    if not hits:
        return
    analysis = analyze_hit(hits[0])
    if analysis is None:
        print("no analyzer for hit")
        return
    grouped = {g.value: d for g, d in analysis.view().as_grouped_dict().items()}
    print(json.dumps(_to_jsonable(grouped), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

