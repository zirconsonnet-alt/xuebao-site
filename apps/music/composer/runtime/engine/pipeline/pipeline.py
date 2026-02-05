from typing import Iterable, List, Tuple
from ..context import GenerationContext
from .stage import Stage
from ....decision.models.interfaces import ScoredCandidate


class Pipeline:
    def __init__(self, stages: Iterable[Stage]):
        self.stages = list(stages)

    def run(
        self,
        ctx: GenerationContext,
        *,
        beam_width: int = 1,
        stage_top_k: int = 0,
    ) -> List[GenerationContext]:
        beam: List[Tuple[GenerationContext, float]] = [(ctx, 0.0)]
        for stage in self.stages:
            candidates: List[Tuple[GenerationContext, float]] = []
            for bctx, acc in beam:
                top_k = stage_top_k if stage_top_k and stage_top_k > 0 else None
                scored: List[ScoredCandidate] = stage.expand(bctx, top_k=top_k)
                scored = list(stage.model.rank(bctx, scored))
                if top_k is not None:
                    scored = scored[:top_k]
                for scored_cand in scored:
                    child = bctx.clone()
                    stage.apply(child, scored_cand.obj)
                    candidates.append((child, acc + scored_cand.score))
            if not candidates:
                return []
            candidates.sort(key=lambda x: x[1], reverse=True)
            beam = candidates[:beam_width]
        return [c for (c, _) in beam]
