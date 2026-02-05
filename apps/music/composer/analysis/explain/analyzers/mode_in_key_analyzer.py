# Analysis explanations for mode in key analyzer
from __future__ import annotations

from ...core.analyzer import Analyzer
from ...core.hits.mode_in_key import ModeInKeyHit
from ....domain.enums.core import Degrees
from ....domain.enums.harmony import VariantForm
from ..analysis.mode_in_key import ModeInKeyAnalysis
from .function_scoring import score_functions_from_intervals, score_function_tendencies
from .chord_in_mode_analyzer import ChordInModeAnalyzer


class ModeInKeyAnalyzer(Analyzer[ModeInKeyHit, ModeInKeyAnalysis]):
    def analyze(self, hit: ModeInKeyHit) -> ModeInKeyAnalysis:
        """Analyze a mode-in-key hit."""
        main_mode = hit.key[hit.key.main_mode_type]
        main_base = main_mode.scale(VariantForm.Base)
        tonic_iv = main_mode.tonic | main_base[Degrees.I]
        third_iv = main_mode.tonic | main_base[Degrees.III]

        skeleton_chord = hit.skeleton_chord()
        present = hit.skeleton_intervals_in_key_main_base()
        function_scores = score_functions_from_intervals(
            present=present,
            tonic_iv=tonic_iv,
            third_iv=third_iv,
        )
        function_tendencies = score_function_tendencies(
            current_scores=function_scores,
            flow=ChordInModeAnalyzer.FUNCTION_TENDENCY_FLOW,
        )
        return ModeInKeyAnalysis(
            hit=hit,
            tonic_interval=hit.tonic_interval(),
            altered_degrees=hit.altered_degrees(),
            skeleton_chord=skeleton_chord,
            skeleton_function_scores=function_scores,
            skeleton_function_tendencies=function_tendencies,
        )
