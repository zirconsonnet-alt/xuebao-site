from __future__ import annotations

from typing import Dict, Set

from ..analysis.chord_in_key import ChordInKeyAnalysis
from ...core.analyzer import Analyzer
from ...core.hits.chord_in_key import ChordInKeyHit
from ....domain.enums.core import Degrees, Intervals
from ....domain.enums.harmony import Functions, VariantForm
from .chord_in_mode_analyzer import ChordInModeAnalyzer
from .function_scoring import score_functions_from_intervals, score_function_tendencies


class ChordInKeyAnalyzer(Analyzer[ChordInKeyHit, ChordInKeyAnalysis]):
    FUNCTION_TENDENCY_FLOW = ChordInModeAnalyzer.FUNCTION_TENDENCY_FLOW

    def analyze(self, hit: ChordInKeyHit) -> ChordInKeyAnalysis:
        function_scores = self.analyze_function(hit)
        function_tendencies = self.analyze_function_tendencies(hit)
        chromatic_score = self.analyze_chromatic_score(hit)
        return ChordInKeyAnalysis(
            hit=hit,
            function_scores=function_scores,
            function_tendencies=function_tendencies,
            chromatic_score=chromatic_score,
        )

    @staticmethod
    def _degree_interval_in_main_base(hit: ChordInKeyHit, deg: Degrees) -> Intervals:
        main_mode = hit.key[hit.key.main_mode_type]
        base = main_mode.scale(VariantForm.Base)
        return main_mode.tonic | base[deg]

    def analyze_function(self, hit: ChordInKeyHit) -> Dict[Functions, float]:
        if not isinstance(hit, ChordInKeyHit):
            raise TypeError("hit 必须为 ChordInKeyHit")
        intervals: Set[Intervals] = set(hit.intervals_in_key_main_base())

        tonic_iv = self._degree_interval_in_main_base(hit, Degrees.I)
        third_iv = self._degree_interval_in_main_base(hit, Degrees.III)
        return score_functions_from_intervals(
            present=intervals,
            tonic_iv=tonic_iv,
            third_iv=third_iv,
        )

    def analyze_function_tendencies(self, hit: ChordInKeyHit) -> Dict[Functions, float]:
        return score_function_tendencies(
            current_scores=self.analyze_function(hit),
            flow=self.FUNCTION_TENDENCY_FLOW,
        )

    @staticmethod
    def analyze_chromatic_score(hit: ChordInKeyHit) -> float:
        return float(len(hit.tonal_semitone_tendencies()))
