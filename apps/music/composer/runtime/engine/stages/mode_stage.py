# Module for mode stage
from ..pipeline.stage import Stage
from ..generators.mode_generator import ModeGenerator
from ....decision.models.baselines.random_policy import RandomPolicy
from ....decision.rules.mode_rules import ModeTransitionRule
from ....domain.relations import ModeId


class ModeStage(Stage):
    def __init__(self, constraints=None, scorers=None, model=None, *, rng=None, domain=None):
        default_constraints = [ModeTransitionRule()]
        super().__init__(
            constraints=constraints or default_constraints,
            scorers=scorers or [],
            model=model or RandomPolicy(),
        )
        self._rng = rng
        self._domain = domain

    def propose(self, ctx):
        if ctx.current_key_id is None:
            return []
        key = ctx.current_key_id.resolve()
        generator = ModeGenerator(rng=ctx.rng if self._rng is None else self._rng)
        prev_mode = None
        if ctx.progression:
            _, prev_mode_id, _ = ctx.progression[-1]
            prev_mode = prev_mode_id.resolve(key)
        return generator.propose(key, self._domain, prev_mode=prev_mode)

    def apply(self, ctx, candidate):
        super().apply(ctx, candidate)
        ctx.current_mode_id = candidate
