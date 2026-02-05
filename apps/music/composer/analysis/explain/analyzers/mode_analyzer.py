# Analysis explanations for mode analyzer
from ..analysis.mode import ModeAnalysis
from ....domain.mode import Mode
from ...core.analyzer import Analyzer


class ModeAnalyzer(Analyzer[Mode, ModeAnalysis]):
    def analyze(self, mode: Mode) -> ModeAnalysis:
        if not isinstance(mode, Mode):
            raise TypeError("mode 必须为 Mode")
        return ModeAnalysis()
