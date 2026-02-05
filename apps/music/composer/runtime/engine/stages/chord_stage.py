from ..pipeline.stage import Stage
from ..generators.chord_generator import ChordGenerator
from ....decision.rules.chord_rules import (
    StartChordRule,
    ResolutionRule,
    FunctionFlowRule,
    TurningPointRule,
    CadenceSDTGoalRule,
    RootNoRepeatRule,
    RootPatternRule,
    RootCadencePositionRule,
    RelativeBaseModeDisambiguationRule,
)
from ....domain.relations import ChordId
from ....decision.models.baselines.random_policy import RandomPolicy
from ....domain.relations import map_degree_to_target_root
from ....runtime.engine.goals import GoalSchedule, can_reach_cadence_sdt


class ChordStage(Stage):
    def __init__(
        self,
        constraints=None,
        scorers=None,
        model=None,
        *,
        rng=None,
        domain=None,
        tcn_model=None,
        tcn_window=8,
    ):
        default_constraints = [
            StartChordRule(),
            ResolutionRule(),
            FunctionFlowRule(),
            TurningPointRule(),
            RelativeBaseModeDisambiguationRule(),
            CadenceSDTGoalRule(),
            RootNoRepeatRule(),
            RootPatternRule(),
            RootCadencePositionRule(),
        ]
        default_scorers = []
        if tcn_model is not None:
            from ....decision.scoring.tcn_step_scorer import TCNLocalScorer

            default_scorers.append(TCNLocalScorer(model=tcn_model, window=tcn_window))
        super().__init__(
            constraints=constraints or default_constraints,
            scorers=default_scorers if scorers is None else scorers,
            model=model or RandomPolicy(),
        )
        self._rng = rng
        self._domain = domain

    def _goal_gate_pass(self, ctx, cand: ChordId) -> bool:
        schedule = getattr(ctx, "goal_schedule", None)
        if not isinstance(schedule, GoalSchedule):
            return True
        if schedule.cadence_sdt is None:
            return True
        mode_id = getattr(ctx, "current_mode_id", None)
        if mode_id is None:
            return True

        idx = len(getattr(ctx, "progression", []) or [])
        next_idx = idx + 1

        # Build last roots (absolute degrees) from history + candidate.
        progression = getattr(ctx, "progression", []) or []
        last_root = None
        if progression:
            _, prev_mode_id, prev_chord_id = progression[-1]
            last_root = map_degree_to_target_root(prev_mode_id, prev_chord_id.degree)

        cand_root = map_degree_to_target_root(mode_id, cand.degree)
        if last_root is not None and cand_root == last_root:
            # Adjacent root repeat is forbidden; no need to run DP.
            return False

        memo = getattr(ctx, "goal_memo", None)
        if memo is None:
            return True

        return can_reach_cadence_sdt(
            schedule,
            next_index=next_idx,
            prev_root=last_root,
            last_root=cand_root,
            memo=memo,
        )

    def propose(self, ctx):
        if ctx.current_key_id is None or ctx.current_mode_id is None:
            return []
        generator = ChordGenerator(rng=ctx.rng if self._rng is None else self._rng)
        mode_id = ctx.current_mode_id
        mode = mode_id.resolve(ctx.current_key_id.resolve())
        return generator.propose(mode, self._domain)

    def expand(self, ctx, top_k=None):
        # Same as Stage.expand, but insert a DP reachability gate between hard_filter and soft_score.
        if top_k is None:
            candidates = self.propose(ctx)
            filtered = self.hard_filter(ctx, candidates)
            gated = [c for c in filtered if isinstance(c, ChordId) and self._goal_gate_pass(ctx, c)]
            scored = self.soft_score(ctx, gated)
            scored.sort(key=lambda x: x.score, reverse=True)
            return scored

        if top_k <= 0:
            return []

        picked = []
        for cand in self.propose(ctx):
            violations = self._check_constraints(ctx, cand)
            if violations:
                for c, v in violations:
                    ctx.audit.add(
                        {
                            "stage": self.__class__.__name__,
                            "candidate": str(cand),
                            "violation_code": v.code,
                            "violation_message": v.message,
                            "constraint": c.__class__.__name__,
                        }
                    )
                continue
            if not isinstance(cand, ChordId):
                continue
            if not self._goal_gate_pass(ctx, cand):
                ctx.audit.add(
                    {
                        "stage": self.__class__.__name__,
                        "candidate": str(cand),
                        "violation_code": "dp_gate",
                        "violation_message": "goal unreachable after candidate",
                        "constraint": "CadenceReachabilityGate",
                    }
                )
                continue
            picked.append(cand)
            if len(picked) >= top_k:
                break

        scored = self.soft_score(ctx, picked)
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def apply(self, ctx, candidate):
        super().apply(ctx, candidate)
        if ctx.current_key_id is None or ctx.current_mode_id is None:
            return
        mode_id = ctx.current_mode_id
        if not isinstance(candidate, ChordId):
            return
        ctx.progression.append((ctx.current_key_id, mode_id, candidate))
        ctx.current_mode_id = None
