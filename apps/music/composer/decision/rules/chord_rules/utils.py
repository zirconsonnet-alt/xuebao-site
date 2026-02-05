# Shared helpers for chord rules
from typing import Optional

from ....domain import Key
from ....domain.relations import ChordId, ChordInfo, KeyId, ModeId


def resolve_key(ctx) -> Optional[Key]:
    key_id = getattr(ctx, "current_key_id", None)
    if isinstance(key_id, KeyId):
        return key_id.resolve()
    return None


def chord_info_from_candidate(ctx, cand) -> Optional[ChordInfo]:
    if cand is None:
        return None
    mode_id = getattr(ctx, "current_mode_id", None)
    if not isinstance(mode_id, ModeId):
        return None
    if not isinstance(cand, ChordId):
        return None
    chord_id = cand
    key_id = getattr(ctx, "current_key_id", None)
    if not isinstance(key_id, KeyId):
        return None
    return (key_id, mode_id, chord_id)
