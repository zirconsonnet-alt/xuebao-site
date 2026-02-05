# Module for sklearn adapter
from typing import Sequence
import numpy as np
from ..interfaces import PolicyModel, ScoredCandidate


class SklearnPolicy(PolicyModel):
    def __init__(self, model) -> None:
        self.model = model

    def _predict_scores(self, candidates: Sequence[ScoredCandidate]) -> Sequence[float]:
        X = np.array([[c.score] for c in candidates], dtype=float)
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)
            if proba.ndim == 2 and proba.shape[1] > 1:
                return proba[:, 1]
            return proba.ravel()
        if hasattr(self.model, "decision_function"):
            return self.model.decision_function(X)
        if hasattr(self.model, "predict"):
            return self.model.predict(X)
        return [c.score for c in candidates]

    def rank(self, ctx, candidates: Sequence[ScoredCandidate]):
        items = list(candidates)
        if not items:
            return items
        scores = self._predict_scores(items)
        ranked = sorted(zip(items, scores), key=lambda x: x[1], reverse=True)
        return [item for item, _ in ranked]

    def choose(self, ctx, candidates: Sequence[ScoredCandidate]):
        ranked = list(self.rank(ctx, candidates))
        if not ranked:
            raise ValueError("no candidates")
        return ranked[0].obj
