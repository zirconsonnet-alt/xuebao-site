import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .audit.report import AuditReport
from ...domain.relations import ChordId, KeyId, ModeId
from .goals import GoalSchedule, ReachabilityMemo


@dataclass
class GenerationContext:
    audit: AuditReport = field(default_factory=AuditReport)
    current_key_id: Optional[KeyId] = None
    current_mode_id: Optional[ModeId] = None
    progression: List[Tuple[KeyId, ModeId, ChordId]] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    goal_schedule: Optional[GoalSchedule] = None
    goal_memo: ReachabilityMemo = field(default_factory=ReachabilityMemo)

    def clone(self) -> "GenerationContext":
        audit = AuditReport(base=self.audit)
        return GenerationContext(
            audit=audit,
            current_key_id=self.current_key_id,
            current_mode_id=self.current_mode_id,
            progression=list(self.progression),
            rng=self.rng,
            goal_schedule=self.goal_schedule,
            goal_memo=self.goal_memo,
        )
