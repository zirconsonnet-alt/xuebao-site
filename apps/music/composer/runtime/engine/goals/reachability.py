from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ....domain.enums.core import Degrees
from .schedule import GoalSchedule


_StateKey = Tuple[str, int, Optional[Degrees], Optional[Degrees]]


@dataclass
class ReachabilityMemo:
    """
    Memo for reachability queries.

    Key: (goalset_id, next_index, prev_root, last_root)
    Value: whether there exists a completion from next_index..end that satisfies hard goals.
    """

    cache: Dict[_StateKey, bool] = field(default_factory=dict)


def can_reach_cadence_sdt(
    schedule: GoalSchedule,
    *,
    next_index: int,
    prev_root: Optional[Degrees],
    last_root: Optional[Degrees],
    memo: ReachabilityMemo,
) -> bool:
    if schedule.cadence_sdt is None:
        return True
    if next_index >= schedule.length:
        return True

    key: _StateKey = (schedule.goalset_id, next_index, prev_root, last_root)
    hit = memo.cache.get(key)
    if hit is not None:
        return hit

    allowed = schedule.cadence_sdt.allowed_roots_at(next_index, length=schedule.length)
    if allowed is None:
        allowed_iter = tuple(Degrees)
    else:
        allowed_iter = tuple(allowed)

    # Relaxed reachability:
    # - Enforce only "no adjacent root repeats" since this is a hard rule today.
    # - Ignore higher-order root pattern / cadence-position rules to avoid false negatives.
    for root in allowed_iter:
        if last_root is not None and root == last_root:
            continue
        if can_reach_cadence_sdt(
            schedule,
            next_index=next_index + 1,
            prev_root=last_root,
            last_root=root,
            memo=memo,
        ):
            memo.cache[key] = True
            return True

    memo.cache[key] = False
    return False
