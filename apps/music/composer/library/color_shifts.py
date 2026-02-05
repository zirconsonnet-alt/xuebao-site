import itertools
from typing import List, Set, Tuple
from ..domain.base_note import BaseNote
from ..domain.key import Key
from ..domain.mode import Mode
from ..domain.color_shift import ColorShift
from ..domain.enums.core import Degrees, NoteNames
from ..domain.enums.harmony import Modes, ModeAccess, VariantForm


def _mode_color_shift(src: Mode, dst: Mode) -> ColorShift:
    src_scale = src.scale(VariantForm.Base)
    dst_scale = dst.scale(VariantForm.Base)
    return src_scale - dst_scale


def _access_modes(key: Key) -> List[Tuple[ModeAccess, Degrees | Modes, Mode]]:
    rel = [(ModeAccess.Relative, d, key[d]) for d in Degrees]
    sub = [(ModeAccess.Substitute, m, key[m]) for m in Modes]
    return rel + sub


def build_color_shifts() -> Set[ColorShift]:
    shifts: Set[ColorShift] = set()
    key = Key(BaseNote(NoteNames.C), Modes.Ionian)
    modes = _access_modes(key)
    for (_, _, src), (_, _, dst) in itertools.permutations(modes, 2):
        shifts.add(_mode_color_shift(src, dst))
    for deg in Degrees:
        rel_mode = key[deg]
        subv_mode = key[(deg, ModeAccess.SubV)]
        shifts.add(_mode_color_shift(subv_mode, rel_mode))
        shifts.add(_mode_color_shift(rel_mode, subv_mode))
    return shifts


_ALL_COLOR_SHIFTS: Set[ColorShift] | None = None


def get_all_color_shifts() -> Set[ColorShift]:
    global _ALL_COLOR_SHIFTS
    if _ALL_COLOR_SHIFTS is None:
        _ALL_COLOR_SHIFTS = build_color_shifts()
    return _ALL_COLOR_SHIFTS
