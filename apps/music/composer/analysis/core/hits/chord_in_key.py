from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set

from ....domain.chord import Chord
from ....domain.base_note import BaseNote
from ....domain.enums.core import Degrees, Intervals
from ....domain.enums.harmony import ModeAccess, Modes, VariantForm
from ....domain.key import Key
from ....domain.mode import Mode
from ....domain.relations import ChordId, ModeId, map_degree_to_target_root
from ...core.hit import ResolveHit, format_degrees, format_role
from ...core.kinds import ResolveKind


@dataclass(frozen=True, slots=True)
class ChordInKeyHit(ResolveHit):
    key: Key
    mode: Mode
    chord: Chord
    mode_id: ModeId
    chord_id: ChordId

    @property
    def access(self) -> ModeAccess:
        return self.mode_id.access

    @property
    def role(self) -> Modes | Degrees:
        return self.mode_id.role

    def chord_degrees_in_mode_scale(self) -> Set[Degrees]:
        comp = frozenset(self.chord_id.composition or frozenset())
        return {self.chord_id.degree + d for d in comp}

    def chord_degrees_in_key_scale(self) -> Set[Degrees]:
        comp = frozenset(self.chord_id.composition or frozenset())
        return {map_degree_to_target_root(self.mode_id, self.chord_id.degree + d) for d in comp}

    def intervals_in_key_main_base(self) -> FrozenSet[Intervals]:
        """
        以 key 主调（key.main_mode_type）的主音为坐标系，计算和弦各音对应的 Intervals 集合。
        这是原子事实：不含权重，仅用于后续功能分析。
        """
        main_mode = self.key[self.key.main_mode_type]
        tonic = main_mode.tonic
        return frozenset(tonic | n for n in self.chord.base_notes)

    def altered_degrees(self) -> FrozenSet[Degrees]:
        """
        相对主调（key.main_mode_type）的 Base 变体，当前 mode 的 Base 变体有哪些 degree 被改变。
        这是“原子事实”，用于解释与审计，不参与权重评分计算。
        """
        main_mode = self.key[self.key.main_mode_type]
        base_scale = self.mode.scale(VariantForm.Base)
        main_base = main_mode.scale(VariantForm.Base)
        role_degree = Degrees.I
        if self.access in (ModeAccess.Relative, ModeAccess.SubV):
            if not isinstance(self.role, Degrees):
                raise TypeError("Relative/SubV 模式的 role 必须为 Degrees")
            role_degree = self.role
        altered = frozenset(
            deg
            for deg in Degrees
            if base_scale[deg - role_degree].offset != main_base[deg].offset
        )
        return altered

    def _chromatic_pitch_classes(self) -> FrozenSet[int]:
        main_mode = self.key[self.key.main_mode_type]
        main_base = main_mode.scale(VariantForm.Base)
        diatonic = frozenset(main_base[deg].offset for deg in Degrees)
        return frozenset(pc for pc in self.chord.pitch_classes if pc not in diatonic)

    @staticmethod
    def _degree_from_root_and_pitch_class(root: BaseNote, target_pitch_class: int) -> Optional[Degrees]:
        best: Optional[tuple[int, Degrees]] = None
        for deg in Degrees:
            note_name = root.note_name + deg  # type: ignore[operator]
            try:
                spelled = BaseNote.from_name_and_offset(note_name, target_pitch_class)
            except ValueError:
                continue
            cand = (abs(spelled.shifts), deg)
            if best is None or cand[0] < best[0] or (cand[0] == best[0] and cand[1].value < best[1].value):
                best = cand
        return None if best is None else best[1]

    def tonal_semitone_tendencies(self) -> Dict[Degrees, List[int]]:
        """
        调性半音倾向性（原子事实）：
        - 只以 key.main_mode_type 的 Base 变体为参照
        - 坐标系：以和弦根音为 Degrees.I（Degrees 为键，类似 composition）
        - 值：目标 pitch class（绝对 0..11），避免坐标系歧义
        """
        main_mode = self.key[self.key.main_mode_type]
        main_base = main_mode.scale(VariantForm.Base)
        diatonic = frozenset(main_base[deg].offset for deg in Degrees)
        result: Dict[Degrees, List[int]] = {}
        root_note = self.chord.scale.tonic
        for pc in sorted(self._chromatic_pitch_classes()):
            src_deg = self._degree_from_root_and_pitch_class(root_note, pc)
            if src_deg is None:
                continue
            targets: List[int] = []
            for t in ((pc + 1) % 12, (pc - 1) % 12):
                if t not in diatonic:
                    continue
                if t not in targets:
                    targets.append(t)
            result[src_deg] = targets
        return result

    @property
    def kind(self) -> ResolveKind:
        return ResolveKind.ChordInKey

    def __str__(self) -> str:
        degs = format_degrees(frozenset(self.chord_id.composition or []))
        return (
            f"[Chord∈Key] chord={self.chord} -> mode={self.mode}[{self.chord_id.variant.name}] "
            f"(access={self.access.name}, role={format_role(self.role)}) in key={self.key}; "
            f"root={self.chord_id.degree.name}, degrees={degs}"
        )
