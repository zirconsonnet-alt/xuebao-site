from dataclasses import dataclass

from .interfaces import Scorer, Score
from .features.sequence_features import build_step_vector, pad_window
from ..models.neural.tcn import TCNScorer
from ...domain.relations import ChordId


@dataclass(frozen=True, slots=True)
class TCNLocalScorer(Scorer):
    model: TCNScorer
    window: int = 8

    def score(self, ctx, candidate) -> Score:
        try:
            import torch  # type: ignore
        except ModuleNotFoundError as e:
            if e.name != "torch":
                raise
            raise ModuleNotFoundError("torch is required for TCNLocalScorer (pip install torch)") from e

        key_id = getattr(ctx, "current_key_id", None)
        mode_id = getattr(ctx, "current_mode_id", None)
        if key_id is None or mode_id is None:
            return Score(0.0)
        key = key_id.resolve()
        mode = mode_id.resolve(key)
        chord_id = candidate if isinstance(candidate, ChordId) else None
        if chord_id is None:
            return Score(0.0)
        chord = chord_id.resolve(mode)

        history_vectors = []
        progression = getattr(ctx, "progression", None) or []
        for kid, mid, cid in progression:
            key_i = kid.resolve()
            mode_i = mid.resolve(key_i)
            chord_i = cid.resolve(mode_i)
            history_vectors.append(build_step_vector(key_i, mode_i, chord_i))
        history_vectors.append(build_step_vector(key, mode, chord))

        window_np = pad_window(history_vectors, window=self.window)
        x = torch.tensor(window_np, dtype=torch.float32).unsqueeze(0)
        x = x.to(next(self.model.parameters()).device)
        with torch.no_grad():
            score = self.model.score_window(x).item()
        return Score(score)
