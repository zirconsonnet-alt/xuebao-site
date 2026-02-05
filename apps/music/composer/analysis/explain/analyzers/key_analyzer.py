# Analysis explanations for key analyzer
from ..analysis.key import KeyAnalysis
from ....domain.key import Key
from ...core.analyzer import Analyzer


class KeyAnalyzer(Analyzer[Key, KeyAnalysis]):
    def analyze(self, key: Key) -> KeyAnalysis:
        if not isinstance(key, Key):
            raise TypeError("key 必须为 Key")
        return KeyAnalysis()
