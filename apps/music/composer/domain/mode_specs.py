from dataclasses import dataclass
from typing import Dict, Tuple, Mapping
from .enums.harmony import Modes, VariantForm
from .enums.core import Degrees, Intervals


IntervalProfile = Tuple[Intervals, ...]


@dataclass(frozen=True, slots=True)
class ModeSpec:
    mode: Modes
    variants: Dict[VariantForm, IntervalProfile]
    characteristic_degree: Degrees


def patch_profile(base: IntervalProfile, changes: Mapping[Degrees, Intervals]) -> IntervalProfile:
    lst = list(base)
    for deg, itv in changes.items():
        idx = deg.value - 1
        lst[idx] = itv
    return tuple(lst)


def make_spec(
    mode: Modes,
    base: IntervalProfile,
    characteristic_degree: Degrees,
    *,
    ascending_changes: Mapping[Degrees, Intervals] | None = None,
    descending_changes: Mapping[Degrees, Intervals] | None = None,
) -> ModeSpec:
    variants: Dict[VariantForm, IntervalProfile] = {VariantForm.Base: base}
    if ascending_changes:
        variants[VariantForm.Ascending] = patch_profile(base, ascending_changes)
    if descending_changes:
        variants[VariantForm.Descending] = patch_profile(base, descending_changes)
    return ModeSpec(mode=mode, variants=variants, characteristic_degree=characteristic_degree)


MODE_SPECS: Dict[Modes, ModeSpec] = {
    Modes.Ionian: make_spec(
        mode=Modes.Ionian,
        base=(Intervals.P1, Intervals.M2, Intervals.M3, Intervals.P4, Intervals.P5, Intervals.M6, Intervals.M7),
        characteristic_degree=Degrees.VII
    ),

    Modes.Dorian: make_spec(
        mode=Modes.Dorian,
        base=(Intervals.P1, Intervals.M2, Intervals.m3, Intervals.P4, Intervals.P5, Intervals.M6, Intervals.m7),
        characteristic_degree=Degrees.VI,
        ascending_changes={Degrees.VII: Intervals.M7},
        descending_changes={Degrees.VI: Intervals.m6},
    ),
    Modes.Phrygian: make_spec(
        mode=Modes.Phrygian,
        base=(Intervals.P1, Intervals.m2, Intervals.m3, Intervals.P4, Intervals.P5, Intervals.m6, Intervals.m7),
        characteristic_degree=Degrees.II,
        ascending_changes={
            Degrees.II: Intervals.M2,
            Degrees.VI: Intervals.M6,
            Degrees.VII: Intervals.M7,
        },
    ),
    Modes.Lydian: make_spec(
        mode=Modes.Lydian,
        base=(Intervals.P1, Intervals.M2, Intervals.M3, Intervals.A4, Intervals.P5, Intervals.M6, Intervals.M7),
        characteristic_degree=Degrees.IV,
    ),
    Modes.Mixolydian: make_spec(
        mode=Modes.Mixolydian,
        base=(Intervals.P1, Intervals.M2, Intervals.M3, Intervals.P4, Intervals.P5, Intervals.M6, Intervals.m7),
        characteristic_degree=Degrees.VII,
        ascending_changes={Degrees.VII: Intervals.M7},
    ),
    Modes.Aeolian: make_spec(
        mode=Modes.Aeolian,
        base=(Intervals.P1, Intervals.M2, Intervals.m3, Intervals.P4, Intervals.P5, Intervals.m6, Intervals.m7),
        characteristic_degree=Degrees.IV,
        ascending_changes={
            Degrees.VI: Intervals.M6,
            Degrees.VII: Intervals.M7,
        },
    ),
    Modes.Locrian: make_spec(
        mode=Modes.Locrian,
        base=(Intervals.P1, Intervals.m2, Intervals.m3, Intervals.P4, Intervals.d5, Intervals.m6, Intervals.m7),
        characteristic_degree=Degrees.V,
    ),
}


def degree_mode(parent: Modes, degree: Degrees) -> Modes:
    if not isinstance(parent, Modes):
        raise TypeError("parent 必须是 Modes")
    if not isinstance(degree, Degrees):
        raise TypeError("degree 必须是 Degrees")
    modes = tuple(Modes)
    i = modes.index(parent)
    shift = degree.value - 1
    j = (i + shift) % len(modes)
    return modes[j]
