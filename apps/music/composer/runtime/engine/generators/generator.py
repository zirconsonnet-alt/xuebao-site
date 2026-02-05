import random
from dataclasses import dataclass
from typing import Callable, Generic, Iterator, List, Optional, TypeVar

T = TypeVar("T")
K = TypeVar("K")


@dataclass(frozen=True, slots=True)
class SamplePlan(Generic[T, K]):
    sample: Callable[[random.Random], T]
    accept: Optional[Callable[[T], bool]] = None
    key: Optional[Callable[[T], K]] = None
    max_tries_per_item: int = 64


class CandidateGenerator(Generic[T, K]):
    def __init__(self, rng: random.Random):
        self.rng = rng

    def propose(self, plan: SamplePlan[T, K], limit: int) -> Iterator[T]:
        if limit <= 0:
            return
        accept = plan.accept
        key_fn = plan.key
        seen: set = set()
        produced = 0
        while produced < limit:
            tries = 0
            got: Optional[T] = None
            while tries < plan.max_tries_per_item:
                cand = plan.sample(self.rng)
                if accept is not None and not accept(cand):
                    tries += 1
                    continue
                if key_fn is None:
                    got = cand
                    break
                k = key_fn(cand)
                if k in seen:
                    tries += 1
                    continue
                seen.add(k)
                got = cand
                break
            if got is None:
                return
            yield got
            produced += 1

    def generate(self, plan: SamplePlan[T, K], limit: int) -> List[T]:
        return list(self.propose(plan, limit))
