from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple, Union
from .enums.core import Degrees, NoteNames
from .enums.harmony import ModeAccess, Modes, VariantForm
from .base_note import BaseNote
from .key import Key
from .mode import Mode
from .chord import Chord


@dataclass(frozen=True, slots=True)
class KeyId:
    tonic: NoteNames
    main_mode_type: Modes

    def resolve(self) -> Key:
        return Key(BaseNote(self.tonic), self.main_mode_type)


@dataclass(frozen=True, slots=True)
class ModeId:
    role: Union[Modes, Degrees]
    access: ModeAccess = ModeAccess.Relative

    def resolve(self, key: Key) -> Mode:
        r = self.role
        if isinstance(r, Modes):
            return key[r]
        if self.access == ModeAccess.Relative:
            return key[r]
        return key[(r, self.access)]


@dataclass(frozen=True, slots=True)
class ChordId:
    degree: Degrees
    variant: VariantForm
    composition: Optional[FrozenSet[Degrees]] = None

    def resolve(self, mode: Mode) -> Chord:
        comp = self.composition
        if comp is None:
            return mode[(self.degree, self.variant)]
        if Degrees.I not in comp:
            raise ValueError("ChordId.composition 必须包含 Degrees.I")
        return mode[(self.degree, self.variant, comp)]


ChordInfo = Tuple[KeyId, ModeId, ChordId]


def _role_from_mode(mode: Union[ModeId, Modes, Degrees]) -> Union[Modes, Degrees]:
    if isinstance(mode, ModeId):
        return mode.role
    return mode


def map_target_root_to_degree(
    mode: Union[ModeId, Modes, Degrees],
    target_root: Degrees,
) -> Degrees:
    role = _role_from_mode(mode)
    if isinstance(role, Degrees):
        return target_root - role
    return target_root


def map_degree_to_target_root(
    mode: Union[ModeId, Modes, Degrees],
    chord_degree: Degrees,
) -> Degrees:
    role = _role_from_mode(mode)
    if isinstance(role, Degrees):
        return chord_degree + role
    return chord_degree
