# Analysis explanations for chord in mode analyzer
from typing import Dict, Set
from ..analysis.chord_in_mode import ChordInModeAnalysis
from ...core.analyzer import Analyzer
from ...core.hits.chord_in_mode import ChordInModeHit
from ....domain.enums.core import Degrees, Intervals
from ....domain.enums.harmony import VariantForm, Functions
from ....domain.enums.runtime import TurningPoints
from .function_scoring import score_functions_from_intervals, score_function_tendencies


class ChordInModeAnalyzer(Analyzer[ChordInModeHit, ChordInModeAnalysis]):
    TURNING_POINT_SCORE: float = 3.0
    FUNCTION_TENDENCY_FLOW: Dict[Functions, Dict[Functions, float]] = {
        Functions.Tonic: {Functions.Subdominant: 0.50},
        Functions.Subdominant: {Functions.Dominant: 0.60},
        Functions.Dominant: {Functions.Tonic: 0.70},
        Functions.Characteristic: {Functions.Tonic: 0.80},
    }

    def analyze(self, chord_hit: ChordInModeHit) -> ChordInModeAnalysis:
        function_scores = self.analyze_function(chord_hit)
        turning_points = self.analyze_turning_points(chord_hit)
        function_tendencies = self.analyze_function_tendencies(chord_hit)
        chromatic_score = self.analyze_chromatic_score(chord_hit)
        analysis = ChordInModeAnalysis(
            hit=chord_hit,
            function_scores=function_scores,
            turning_points=turning_points,
            function_tendencies=function_tendencies,
            chromatic_score=chromatic_score,
        )
        return analysis

    @staticmethod
    def _degree_interval_in_mode_base(hit: ChordInModeHit, deg: Degrees) -> Intervals:
        base = hit.mode.scale(VariantForm.Base)
        return hit.mode.tonic | base[deg]

    def analyze_function(self, hit: ChordInModeHit) -> Dict[Functions, float]:
        if not isinstance(hit, ChordInModeHit):
            raise TypeError("hit 必须为 ChordInModeHit")

        # 以调式主音为坐标系计算 Intervals 集合（区分 M7 vs m7）
        intervals: Set[Intervals] = {hit.mode.tonic | n for n in hit.chord.base_notes}

        tonic_iv = self._degree_interval_in_mode_base(hit, Degrees.I)
        third_iv = self._degree_interval_in_mode_base(hit, Degrees.III)
        return score_functions_from_intervals(present=intervals, tonic_iv=tonic_iv, third_iv=third_iv)

    def analyze_function_tendencies(self, hit: ChordInModeHit) -> Dict[Functions, float]:
        if not isinstance(hit, ChordInModeHit):
            raise TypeError("hit 必须为 ChordInModeHit")
        return score_function_tendencies(current_scores=self.analyze_function(hit), flow=self.FUNCTION_TENDENCY_FLOW)

    def analyze_turning_points(self, hit: ChordInModeHit) -> Set[TurningPoints]:
        if not isinstance(hit, ChordInModeHit):
            raise TypeError("hit 必须为 ChordInModeHit")
        return set(hit.turning_points())

    def analyze_chromatic_score(self, hit: ChordInModeHit) -> float:
        if not isinstance(hit, ChordInModeHit):
            raise TypeError("hit 必须为 ChordInModeHit")
        if hit.chord_id.variant == VariantForm.Base:
            return 0.0
        chord_degrees: Set[Degrees] = self.chord_degrees_in_mode_scale(hit)
        base_scale = hit.mode.scale(VariantForm.Base)
        cur_scale = hit.mode.scale(hit.chord_id.variant)
        score = 0.0
        for deg in chord_degrees:
            if cur_scale[deg].offset != base_scale[deg].offset:
                score += 1.0
        return score

    @staticmethod
    def chord_degrees_in_mode_scale(hit: ChordInModeHit) -> Set[Degrees]:
        if not isinstance(hit, ChordInModeHit):
            raise TypeError("hit 必须为 ChordInModeHit")
        comp = hit.chord_id.composition or frozenset()
        return {hit.chord_id.degree + d for d in comp}
