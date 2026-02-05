# Analysis explanations for chord analyzer
from __future__ import annotations

from typing import DefaultDict, Optional
from collections import defaultdict

from ....domain.base_note import BaseNote
from ....domain.chord import Chord
from ....domain.dissonance import Resolution
from ....domain.enums.core import Degrees
from ...core.analyzer import Analyzer
from ..analysis.chord import ChordAnalysis

_TENSION_FULL_SCALE_PRIORITY_SUM = 150.0
_PRIORITY_TO_TENDENCY_WEIGHT = 50.0


def _clip_0_10(value: float) -> float:
    if value <= 0:
        return 0.0
    if value >= 10:
        return 10.0
    return float(value)


def _step_targets(pitch_class: int, resolution: Resolution) -> tuple[int, ...]:
    if resolution == Resolution.STEP_UP:
        return ((pitch_class + 1) % 12, (pitch_class + 2) % 12)
    if resolution == Resolution.STEP_DOWN:
        return ((pitch_class - 1) % 12, (pitch_class - 2) % 12)
    if resolution == Resolution.STEP_EITHER:
        return (
            (pitch_class + 1) % 12,
            (pitch_class + 2) % 12,
            (pitch_class - 1) % 12,
            (pitch_class - 2) % 12,
        )
    return ()


def _degree_from_root_and_pitch_class(root: BaseNote, target_pitch_class: int) -> Optional[Degrees]:
    """
    以和弦根音为 Degrees.I 的坐标系，把 target_pitch_class 映射为 Degrees。

    注意：这里 Degrees 只表示“字母级数”，忽略升降号差异；
    选择规则：在 BaseNote.MAX_SHIFTS 约束下，优先选择升降号数量更少的拼写；并列时按 Degrees 顺序稳定选取。
    """
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


class ChordAnalyzer(Analyzer[Chord, ChordAnalysis]):
    def analyze(self, chord: Chord) -> ChordAnalysis:
        relations = chord.quality.dissonance_relations
        priority_sum = float(sum(rel.priority for rel in relations))
        tension_score = _clip_0_10(10.0 * priority_sum / _TENSION_FULL_SCALE_PRIORITY_SUM)

        root_note = chord.scale.tonic
        root_pitch_class = root_note.offset
        target_note_tendencies: DefaultDict[Degrees, float] = defaultdict(float)
        for rel in relations:
            w = float(rel.priority) / _PRIORITY_TO_TENDENCY_WEIGHT
            for interval, res in rel.resolution:
                if res == Resolution.NONE:
                    continue
                source_pitch_class = (root_pitch_class + interval.semitones) % 12
                for target_pc in _step_targets(source_pitch_class, res):
                    deg = _degree_from_root_and_pitch_class(root_note, target_pc)
                    if deg is None:
                        continue
                    target_note_tendencies[deg] += w

        return ChordAnalysis(
            chord=chord,
            tension_score=tension_score,
            target_note_tendencies=dict(target_note_tendencies),
        )
