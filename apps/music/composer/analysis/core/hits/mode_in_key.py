# Module for mode in key hits
from dataclasses import dataclass
from typing import FrozenSet

from ....domain.chord import Chord
from ....domain.key import Key
from ....domain.mode import Mode
from ....domain.enums.core import Degrees, Intervals
from ....domain.enums.harmony import ModeAccess, Modes, VariantForm
from ....domain.relations import ChordId
from ...core.hit import ResolveHit, format_role
from ...core.kinds import ResolveKind


@dataclass(frozen=True, slots=True)
class ModeInKeyHit(ResolveHit):
    key: Key
    mode: Mode
    access: ModeAccess
    role: Modes | Degrees

    def skeleton_chord(self) -> Chord:
        """
        调式骨架和弦：永远取该 mode 的 I 级主三和弦（Base 变体）。
        这是原子事实（不含权重）。
        """
        return ChordId(
            degree=Degrees.I,
            variant=VariantForm.Base,
            composition=frozenset({Degrees.I, Degrees.III, Degrees.V}),
        ).resolve(self.mode)

    def skeleton_intervals_in_key_main_base(self) -> FrozenSet[Intervals]:
        """
        以 key 主调（key.main_mode_type）的主音为坐标系，计算 skeleton_chord 各音对应的 Intervals 集合。
        这是原子事实（不含权重）。
        """
        main_mode = self.key[self.key.main_mode_type]
        tonic = main_mode.tonic
        chord = self.skeleton_chord()
        return frozenset(tonic | n for n in chord.base_notes)

    def tonic_interval(self) -> int:
        main_mode = self.key[self.key.main_mode_type]
        return (self.mode.tonic.offset - main_mode.tonic.offset) % 12

    def altered_degrees(self) -> FrozenSet[Degrees]:
        main_mode = self.key[self.key.main_mode_type]
        base_scale = self.mode.scale(VariantForm.Base)
        main_base = main_mode.scale(VariantForm.Base)
        role_degree = Degrees.I
        if self.access in (ModeAccess.Relative, ModeAccess.SubV):
            if not isinstance(self.role, Degrees):
                raise TypeError("Relative/SubV 模式的 role 必须为 Degrees")
            role_degree = self.role
        elif self.access == ModeAccess.Substitute:
            role_degree = Degrees.I
        altered = frozenset(
            deg
            for deg in Degrees
            if base_scale[deg - role_degree].offset != main_base[deg].offset
        )
        return altered

    @property
    def kind(self) -> ResolveKind:
        return ResolveKind.ModeInKey

    def __str__(self) -> str:
        return (
            f"[Mode∈Key] mode={self.mode} -> access={self.access.name}, "
            f"role={format_role(self.role)} in key={self.key}"
        )
