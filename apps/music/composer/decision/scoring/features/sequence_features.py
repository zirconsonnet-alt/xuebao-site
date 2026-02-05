from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

from ....analysis.api.vector import vectorize_key, vectorize_mode, vectorize_chord
from ....domain.key import Key
from ....domain.mode import Mode
from ....domain.chord import Chord
from ....domain.relations import ChordId, KeyId, ModeId
from ...models.neural.tcn import TCNScorer


@dataclass(frozen=True, slots=True)
class SequenceFeaturesConfig:
    tcn_pool: str = "mean"  # mean/last
    tail_k: int = 4
    worst_k: int = 2
    include_tcn_embedding: bool = True


def _coerce_mode(item) -> Mode:
    if isinstance(item, Mode):
        return item
    raise TypeError("mode item must be Mode")


def build_step_vector(key: Key, mode, chord: Chord) -> List[float]:
    mode = _coerce_mode(mode)
    key_vec = vectorize_key(key)
    mode_vec = vectorize_mode(mode, key=key)
    chord_vec = vectorize_chord(chord, mode=mode)
    return list(key_vec) + list(mode_vec) + list(chord_vec)


def resolve_sequence(
    progression: Sequence[Tuple[KeyId, ModeId, ChordId]],
) -> Tuple[Key, List[Mode], List[Chord]]:
    if not progression:
        raise ValueError("progression is empty")
    key = progression[0][0].resolve()
    modes: List[Mode] = []
    chords: List[Chord] = []
    for key_id, mode_id, chord_id in progression:
        key_i = key_id.resolve()
        mode = mode_id.resolve(key_i)
        chord = chord_id.resolve(mode)
        modes.append(mode)
        chords.append(chord)
    return key, modes, chords


def build_sequence_vectors(key: Key, modes: Sequence, chords: Sequence[Chord]) -> List[List[float]]:
    return [build_step_vector(key, _coerce_mode(m), c) for m, c in zip(modes, chords)]


def pad_window(vectors: Sequence[Sequence[float]], *, window: int) -> np.ndarray:
    if not vectors:
        return np.zeros((window, 0), dtype=np.float32)
    dim = len(vectors[0])
    pad = max(0, window - len(vectors))
    trimmed = list(vectors[-window:])
    if pad:
        return np.vstack([np.zeros((pad, dim), dtype=np.float32), np.array(trimmed, dtype=np.float32)])
    return np.array(trimmed, dtype=np.float32)


def sequence_stats(scores: np.ndarray, worst_k: int) -> dict:
    if scores.size == 0:
        return {
            "tcn_mean": 0.0,
            "tcn_min": 0.0,
            "tcn_std": 0.0,
            "tcn_last": 0.0,
            "tcn_worst_k_mean": 0.0,
        }
    worst_k = max(1, min(worst_k, scores.size))
    worst = np.sort(scores)[:worst_k]
    return {
        "tcn_mean": float(scores.mean()),
        "tcn_min": float(scores.min()),
        "tcn_std": float(scores.std()),
        "tcn_last": float(scores[-1]),
        "tcn_worst_k_mean": float(worst.mean()),
    }


def extract_sequence_features(
    *,
    progression: Sequence[Tuple[KeyId, ModeId, ChordId]],
    tcn: TCNScorer,
    config: SequenceFeaturesConfig,
) -> dict:
    try:
        import torch  # type: ignore
    except ModuleNotFoundError as e:
        if e.name != "torch":
            raise
        raise ModuleNotFoundError("torch is required for extract_sequence_features (pip install torch)") from e

    if not progression:
        return {"seq_len": 0, **sequence_stats(np.array([], dtype=np.float32), config.worst_k)}
    key, modes, chords = resolve_sequence(progression)
    vectors = build_sequence_vectors(key, modes, chords)
    x = torch.tensor(vectors, dtype=torch.float32).unsqueeze(0)  # (1, T, D)
    device = next(tcn.parameters()).device
    x = x.to(device)
    with torch.no_grad():
        step_scores = tcn.forward(x, return_sequence=True).squeeze(0).cpu().numpy()
    features = {"seq_len": len(vectors), **sequence_stats(step_scores, config.worst_k)}

    if config.include_tcn_embedding:
        with torch.no_grad():
            emb = tcn.embed(x, pool=config.tcn_pool)
        emb = emb.squeeze(0).cpu().numpy()
        for i, v in enumerate(emb.tolist()):
            features[f"tcn_emb_{i}"] = float(v)

    return features


def to_feature_vector(feature_dict: dict, ordered_keys: Sequence[str]) -> np.ndarray:
    return np.array([feature_dict.get(k, 0.0) for k in ordered_keys], dtype=np.float32)
