import random
from typing import Callable, List, Optional, Tuple

from .context import GenerationContext
from .pipeline import Pipeline
from .stages import ChordStage, KeyStage, ModeStage
from ...domain.relations import ChordId, KeyId, ModeId
from .goals import GoalSchedule

Triplet = Tuple[KeyId, ModeId, ChordId]


def build_triplet_stages(
    length: int,
    *,
    per_step_key: bool = False,
    key_stage_factory: Optional[Callable[[], KeyStage]] = None,
    mode_stage_factory: Optional[Callable[[], ModeStage]] = None,
    chord_stage_factory: Optional[Callable[[], ChordStage]] = None,
) -> List[object]:
    if length <= 0:
        return []
    key_stage_factory = key_stage_factory or (lambda: KeyStage())
    mode_stage_factory = mode_stage_factory or (lambda: ModeStage())
    chord_stage_factory = chord_stage_factory or (lambda: ChordStage())

    stages: List[object] = []
    if not per_step_key:
        stages.append(key_stage_factory())
    for _ in range(length):
        if per_step_key:
            stages.append(key_stage_factory())
        stages.append(mode_stage_factory())
        stages.append(chord_stage_factory())
    return stages


def generate_triplets(
    length: int,
    *,
    beam_width: int = 5,
    stage_budget: int = 50,
    max_attempts: int = 6,
    budget_growth: int = 2,
    seed: Optional[int] = None,
    per_step_key: bool = False,
    fallback_full_scan: bool = True,
    goal_schedule: Optional[GoalSchedule] = None,
) -> List[Triplet]:
    if length <= 0:
        return []
    if beam_width <= 0:
        raise ValueError("beam_width 必须 > 0")
    if stage_budget <= 0:
        raise ValueError("stage_budget 必须 > 0")
    if max_attempts <= 0:
        raise ValueError("max_attempts 必须 > 0")
    if budget_growth <= 0:
        raise ValueError("budget_growth 必须 > 0")

    for i in range(max_attempts):
        budget = stage_budget * (budget_growth**i)
        rng = random.Random(seed + i) if seed is not None else random.Random()
        ctx = GenerationContext(rng=rng, goal_schedule=goal_schedule)
        stages = build_triplet_stages(length, per_step_key=per_step_key)
        beam = Pipeline(stages).run(ctx, beam_width=beam_width, stage_top_k=budget)
        if beam:
            return beam[0].progression

    if fallback_full_scan:
        rng = random.Random(seed) if seed is not None else random.Random()
        ctx = GenerationContext(rng=rng, goal_schedule=goal_schedule)
        stages = build_triplet_stages(length, per_step_key=per_step_key)
        beam = Pipeline(stages).run(ctx, beam_width=beam_width, stage_top_k=0)
        if beam:
            return beam[0].progression

    raise RuntimeError("无解：在当前规则/预算下没有可行序列")
