# Module for key stage
from ..pipeline.stage import Stage
from typing import List, Optional

from ..generators.key_generator import KeyGenerator
from ....decision.models.baselines.random_policy import RandomPolicy
from ....domain.relations import KeyId


class KeyStage(Stage):
    def __init__(
        self,
        constraints=None,
        scorers=None,
        model=None,
        *,
        candidates: Optional[List[KeyId]] = None,
        candidate_pool_size: int = 5,
    ):
        super().__init__(
            constraints=constraints or [],
            scorers=scorers or [],
            model=model or RandomPolicy(),
        )
        self._candidates = candidates
        self._candidate_pool_size = candidate_pool_size

    def propose(self, ctx):
        generator = KeyGenerator(
            candidates=self._candidates,
            candidate_pool_size=self._candidate_pool_size,
            rng=ctx.rng,
        )
        return generator.propose()

    def apply(self, ctx, candidate):
        super().apply(ctx, candidate)
        ctx.current_key_id = candidate
