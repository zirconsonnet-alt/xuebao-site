# Module for stage
from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Sequence, Optional, Tuple
from ..context import GenerationContext
from ....decision.rules.constraints import Constraint, Violation
from ....decision.scoring.interfaces import Scorer
from ....decision.models.interfaces import PolicyModel, ScoredCandidate


class Stage(ABC):
    def __init__(self, constraints: Iterable[Constraint], scorers: Iterable[Scorer], model: PolicyModel):
        self.constraints = list(constraints)
        self.scorers = list(scorers)
        self.model = model

    @abstractmethod
    def propose(self, ctx: GenerationContext) -> Iterable[Any]:
        raise NotImplementedError

    def _check_constraints(self, ctx: GenerationContext, cand: Any) -> List[Tuple[Constraint, Violation]]:
        violations: List[tuple[Constraint, Violation]] = []
        for c in self.constraints:
            v = c.check(ctx, cand)
            if v is not None:
                violations.append((c, v))
        return violations

    def hard_filter(self, ctx: GenerationContext, candidates: Iterable[Any]) -> List[Any]:
        passed: List[Any] = []
        for cand in candidates:
            violations = self._check_constraints(ctx, cand)
            if not violations:
                passed.append(cand)
                continue
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
        return passed

    def _score_one(self, ctx: GenerationContext, cand: Any) -> ScoredCandidate:
        value = 0.0
        evidence: List[Any] = []
        for s in self.scorers:
            res = s.score(ctx, cand)
            value += res.value
            if res.evidence is not None:
                evidence.append(res.evidence)
            ctx.audit.add(
                {
                    "stage": self.__class__.__name__,
                    "candidate": str(cand),
                    "scorer": s.__class__.__name__,
                    "score": res.value,
                }
            )
        return ScoredCandidate(obj=cand, score=value, evidence=evidence or None)

    def soft_score(self, ctx: GenerationContext, candidates: Iterable[Any]) -> List[ScoredCandidate]:
        scored: List[ScoredCandidate] = []
        for cand in candidates:
            scored.append(self._score_one(ctx, cand))
        return scored

    def expand(self, ctx: GenerationContext, top_k: Optional[int] = None) -> List[ScoredCandidate]:
        # 默认行为：完整展开并对全部候选评分排序（保持历史语义）。
        if top_k is None:
            candidates = self.propose(ctx)
            filtered = self.hard_filter(ctx, candidates)
            scored = self.soft_score(ctx, filtered)
            scored.sort(key=lambda x: x.score, reverse=True)
            return scored

        # 启用 top_k 时：把它视为“采样/评分预算 M”而非“全局最优 top_k”。
        # 从候选流中按顺序取前 M 个通过硬约束的候选，然后只对这 M 个做 soft score 与排序。
        if top_k <= 0:
            return []

        picked: List[Any] = []
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
            picked.append(cand)
            if len(picked) >= top_k:
                break

        scored = self.soft_score(ctx, picked)
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def choose(self, ctx: GenerationContext, scored: Sequence[ScoredCandidate]) -> Any:
        return self.model.choose(ctx, scored)

    def apply(self, ctx: GenerationContext, candidate: Any) -> None:
        return None

    def run(self, ctx: GenerationContext) -> Any:
        candidates = self.propose(ctx)
        filtered = self.hard_filter(ctx, candidates)
        scored = self.soft_score(ctx, filtered)
        return self.choose(ctx, scored)
