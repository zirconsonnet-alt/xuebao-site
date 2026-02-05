from typing import Dict, Set, Tuple, Union, overload, AbstractSet, FrozenSet
from .base_note import BaseNote
from .scale import Scale
from .chord import Chord
from .enums.core import Degrees, Intervals
from .enums.harmony import Modes, VariantForm, Tonality
from .mode_specs import MODE_SPECS, ModeSpec
from ._intern import InternedMeta, FrozenSlotsMixin


class Mode(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("tonic", "mode_type", "_spec", "_scales", "__weakref__")

    @classmethod
    def _cache_key(cls, tonic: BaseNote, mode_type: Modes):
        return tonic, mode_type

    def __init__(self, tonic: BaseNote, mode_type: Modes):
        if not isinstance(mode_type, Modes):
            raise TypeError("mode_type 必须为 Modes")
        if (spec := MODE_SPECS.get(mode_type)) is None:
            raise ValueError(f"未知 mode_type: {mode_type}")
        self.tonic = tonic
        self.mode_type = mode_type
        self._spec: ModeSpec = spec
        self._scales: Dict[VariantForm, Scale] = {
            v: Scale(tonic, spec.variants[v]) for v in spec.variants
        }
        self._freeze()

    @property
    def spec(self) -> ModeSpec:
        return self._spec

    def __str__(self) -> str:
        return f"{self.tonic}-{self.mode_type.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mode):
            return NotImplemented
        return self.tonic == other.tonic and self.mode_type == other.mode_type

    def __hash__(self) -> int:
        return hash((self.tonic, self.mode_type.value))

    def scale_of(self, degree: Degrees, variant: VariantForm = VariantForm.Base) -> Scale:
        if not isinstance(degree, Degrees):
            raise TypeError("degree 必须为 Degrees")
        if not isinstance(variant, VariantForm):
            raise TypeError("variant 必须为 VariantForm")
        # Variant-first semantics:
        # - First pick the pitch collection by `variant` on the current mode.
        # - Then derive a new scale by rotating within the SAME collection on `degree`.
        #
        # This matches the expectation that, e.g., Aeolian(Ascending) is a single collection
        # (melodic minor), and "degree V" should be a rotation of that collection,
        # not "derived mode type (Phrygian) with its own Ascending variant profile".
        if variant not in self._scales:
            raise ValueError(f"{self.mode_type.name} 不支持 variant: {variant.name}")

        parent_scale = self._scales[variant]
        derived_tonic = parent_scale[degree]

        def _rotated_note(target_degree: Degrees) -> BaseNote:
            # Map target_degree (I..VII) in derived scale to a degree in parent_scale.
            return parent_scale[degree + (target_degree - Degrees.I)]

        intervals = tuple(derived_tonic | _rotated_note(d) for d in Degrees)
        if intervals[0] != Intervals.P1:
            raise ValueError("派生音阶构造失败：I 级必须为 P1")
        return Scale(derived_tonic, intervals)

    def scale(self, variant: VariantForm = VariantForm.Base) -> Scale:
        return self.scale_of(Degrees.I, variant)

    @overload
    def __getitem__(self, key: Tuple[Degrees, VariantForm]) -> Chord: ...
    @overload
    def __getitem__(self, key: Tuple[Degrees, VariantForm, AbstractSet[Degrees]]) -> Chord: ...

    def __getitem__(
        self,
        key: Union[Tuple[Degrees, VariantForm], Tuple[Degrees, VariantForm, AbstractSet[Degrees]]],
    ) -> Chord:
        if isinstance(key, tuple) and len(key) == 2:
            degree, variant = key
            sc = self.scale_of(degree, variant)
            return Chord(sc)
        if isinstance(key, tuple) and len(key) == 3:
            degree, variant, composition = key
            sc = self.scale_of(degree, variant)
            return Chord(sc, composition)
        raise KeyError(f"Mode 没有这个键: {key!r}")

    def __contains__(self, key: Union[BaseNote, Scale, Chord]) -> bool:
        if isinstance(key, BaseNote):
            return len(self | key) > 0
        if isinstance(key, Scale):
            return len(self | key) > 0
        if isinstance(key, Chord):
            return len(self | key) > 0
        return False

    def __or__(self, key: Union[BaseNote, Scale, Chord]) -> Set[Tuple[Degrees, VariantForm]]:
        result: Set[Tuple[Degrees, VariantForm]] = set()
        if isinstance(key, BaseNote):
            for variant in self._scales.keys():
                for degree in Degrees:
                    if key in self.scale_of(degree, variant):
                        result.add((degree, variant))
            return result
        if isinstance(key, Scale):
            for variant in self._scales.keys():
                for degree in Degrees:
                    if self.scale_of(degree, variant) == key:
                        result.add((degree, variant))
            return result
        if isinstance(key, Chord):
            for variant in self._scales.keys():
                for degree in Degrees:
                    if self.scale_of(degree, variant) == key.scale:
                        result.add((degree, variant))
            return result
        return result

    @property
    def characteristic_degree(self) -> Degrees:
        return self.spec.characteristic_degree

    @property
    def tonality(self) -> Tonality:
        base_intervals = self.spec.variants[VariantForm.Base]
        third = base_intervals[2]
        return Tonality.maj if third == Intervals.M3 else Tonality.min
