from typing import Dict, Tuple, Union, overload, Set, Optional
from types import MappingProxyType
from .mode import Mode
from .scale import Scale
from .base_note import BaseNote
from .chord import Chord
from .mode_specs import degree_mode
from .enums.core import Degrees, Intervals
from .enums.harmony import VariantForm, Modes, ModeAccess
from ._intern import InternedMeta, FrozenSlotsMixin


ModeIndex = Tuple[Degrees, ModeAccess]


class Key(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("tonic", "main_mode_type", "modes_by_type", "modes_by_degree", "_modes_by_type", "_modes_by_degree", "__weakref__")

    @classmethod
    def _cache_key(cls, tonic: BaseNote, main_mode_type: Modes):
        return tonic, main_mode_type

    def __init__(self, tonic: BaseNote, main_mode_type: Modes):
        if not isinstance(main_mode_type, Modes):
            raise ValueError(f"不支持的主调式类型: {main_mode_type}")
        self.tonic = tonic
        self.main_mode_type = main_mode_type
        modes_by_type, modes_by_degree = self._build_modes()
        self._modes_by_type = modes_by_type
        self._modes_by_degree = modes_by_degree
        self.modes_by_type = MappingProxyType(modes_by_type)
        self.modes_by_degree = MappingProxyType(modes_by_degree)
        self._freeze()

    def __str__(self) -> str:
        return f"{self[self.main_mode_type]}调性"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Key):
            return NotImplemented
        return other.tonic == self.tonic and other.main_mode_type == self.main_mode_type

    def __hash__(self) -> int:
        return hash((self.tonic, self.main_mode_type.value))

    def __contains__(self, key: Union[Mode, Scale, BaseNote, Chord]) -> bool:
        if isinstance(key, Mode):
            return self | key is not None
        if isinstance(key, (Scale, BaseNote, Chord)):
            return bool(self | key)
        return False

    def __or__(self, key: Union[Mode, Scale, BaseNote, Chord]) \
            -> Optional[Union[Modes, Degrees, Set[Union[Modes, Degrees]]]]:
        if isinstance(key, Mode):
            for mt, m in self.modes_by_type.items():
                if m == key:
                    return mt
            for deg, m in self.modes_by_degree.items():
                if m == key:
                    return deg
            return None
        if isinstance(key, (Scale, BaseNote, Chord)):
            hits: Set[Union[Modes, Degrees]] = set()
            for mt, m in self.modes_by_type.items():
                if key in m:
                    hits.add(mt)
            for deg, m in self.modes_by_degree.items():
                if key in m:
                    hits.add(deg)
            return hits
        return None

    def __sub__(self, other: "Key") -> Set[Union[Degrees, Modes]]:
        result: Set[Union[Degrees, Modes]] = set()
        for mt, m in self.modes_by_type.items():
            if m not in other.modes_by_type.values():
                result.add(mt)
        for deg, m in self.modes_by_degree.items():
            if m not in other.modes_by_degree.values():
                result.add(deg)
        return result

    @overload
    def __getitem__(self, key: Modes) -> Mode: ...
    @overload
    def __getitem__(self, key: Degrees) -> Mode: ...
    @overload
    def __getitem__(self, key: ModeIndex) -> Mode: ...

    def __getitem__(self, key: Union[Modes, Degrees, ModeIndex]) -> Mode:
        if isinstance(key, Modes):
            return self.modes_by_type[key]
        if isinstance(key, Degrees):
            return self.modes_by_degree[key]
        if isinstance(key, tuple) and len(key) == 2:
            degree, access = key
            if not isinstance(degree, Degrees) or not isinstance(access, ModeAccess):
                raise KeyError(f"Key 没有这个键: {key!r}")
            if access == ModeAccess.Relative:
                return self.modes_by_degree[degree]
            if access == ModeAccess.SubV:
                return self._get_sub_mode_of_degree(degree)
            raise KeyError(f"Key 未处理的 ModeAccess: {access!r}")
        raise KeyError(f"Key 没有这个键: {key!r}")

    def _get_sub_mode_of_degree(self, degree: Degrees) -> Mode:
        if not isinstance(degree, Degrees):
            raise TypeError("degree 必须为 Degrees")
        main_scale = self.modes_by_type[self.main_mode_type].scale(VariantForm.Base)
        target = main_scale[degree]
        sub_root = target + Intervals.m2
        return Mode(sub_root, Modes.Mixolydian)

    def _build_modes(self) -> Tuple[Dict[Modes, Mode], Dict[Degrees, Mode]]:
        modes_by_type: Dict[Modes, Mode] = {mt: Mode(self.tonic, mt) for mt in Modes}
        main_mode = modes_by_type[self.main_mode_type]
        main_scale = main_mode.scale(VariantForm.Base)
        modes_by_degree: Dict[Degrees, Mode] = {}
        for degree in Degrees:
            mode_type = degree_mode(self.main_mode_type, degree)
            tonic = main_scale[degree]
            modes_by_degree[degree] = Mode(tonic, mode_type)
        return modes_by_type, modes_by_degree
