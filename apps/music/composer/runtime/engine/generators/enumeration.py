import random
from dataclasses import dataclass
from typing import Callable, Generic, Iterator, List, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")
V = TypeVar("V")


class LazyShuffler(Generic[V]):
    def __init__(self, items: Sequence[V], rng: random.Random):
        self._items = items
        self._rng = rng
        self._n = len(items)
        self._i = 0
        self._swaps: dict[int, int] = {}

    def __iter__(self) -> "LazyShuffler[V]":
        return self

    def __next__(self) -> V:
        if self._i >= self._n:
            raise StopIteration
        i = self._i
        j = self._rng.randrange(i, self._n)
        a = self._swaps.get(i, i)
        b = self._swaps.get(j, j)
        self._swaps[i] = b
        self._swaps[j] = a
        self._i += 1
        idx = self._swaps.get(i, i)
        return self._items[idx]


@dataclass(frozen=True, slots=True)
class RelationSpec(Generic[T]):
    depth: int
    roots: Callable[[], Sequence[object]]
    children: Callable[[Tuple[object, ...]], Sequence[object]]
    forbidden: Callable[[Tuple[object, ...], object], bool]
    assemble: Callable[[Tuple[object, ...]], T]


class PrefixEnumerator(Generic[T]):
    def __init__(self, spec: RelationSpec[T], rng: random.Random, *, window: int = 16):
        self._spec = spec
        self._rng = rng
        self._window = max(1, int(window))

    def propose(self, limit: int) -> Iterator[T]:
        if limit <= 0:
            return

        depth = self._spec.depth
        if depth <= 0:
            return

        def iter_layer(prefix: Tuple[object, ...], items: Sequence[object]) -> Iterator[object]:
            filtered = [v for v in items if not self._spec.forbidden(prefix, v)]
            return iter(LazyShuffler(filtered, self._rng)) if filtered else iter(())

        def chain_first(f: object, it: Iterator[object]) -> Iterator[object]:
            yield f
            yield from it

        if depth == 1:
            produced = 0
            root_iter = iter_layer((), self._spec.roots())
            while produced < limit:
                try:
                    a = next(root_iter)
                except StopIteration:
                    return
                yield self._spec.assemble((a,))
                produced += 1
            return

        prefix_depth = depth - 1

        def iter_prefixes() -> Iterator[Tuple[object, ...]]:
            prefix: List[object] = []
            stack: List[Iterator[object]] = [iter_layer((), self._spec.roots())]
            while stack:
                try:
                    v = next(stack[-1])
                except StopIteration:
                    stack.pop()
                    if prefix:
                        prefix.pop()
                    continue

                prefix.append(v)

                if len(prefix) == prefix_depth:
                    yield tuple(prefix)
                    prefix.pop()
                    continue

                child_prefix = tuple(prefix)
                child_iter = iter_layer(child_prefix, self._spec.children(child_prefix))
                try:
                    first = next(child_iter)
                except StopIteration:
                    prefix.pop()
                    continue
                stack.append(chain_first(first, child_iter))

        @dataclass
        class _PrefixState:
            prefix: Tuple[object, ...]
            it: Iterator[object]

        def make_state(pfx: Tuple[object, ...]) -> Optional[_PrefixState]:
            it = iter_layer(pfx, self._spec.children(pfx))
            try:
                first = next(it)
            except StopIteration:
                return None
            return _PrefixState(prefix=pfx, it=chain_first(first, it))

        produced = 0
        prefixes = iter_prefixes()
        prefixes_exhausted = False
        active: List[_PrefixState] = []
        last_idx = -1

        def top_up() -> None:
            nonlocal prefixes_exhausted
            while not prefixes_exhausted and len(active) < self._window:
                try:
                    pfx = next(prefixes)
                except StopIteration:
                    prefixes_exhausted = True
                    return
                st = make_state(pfx)
                if st is not None:
                    active.append(st)

        while produced < limit:
            top_up()
            if not active:
                return

            if len(active) == 1:
                idx = 0
            else:
                idx = self._rng.randrange(0, len(active))
                if idx == last_idx:
                    idx = (idx + 1 + self._rng.randrange(0, len(active) - 1)) % len(active)

            state = active[idx]
            try:
                leaf = next(state.it)
            except StopIteration:
                active[idx] = active[-1]
                active.pop()
                if last_idx == idx:
                    last_idx = -1
                continue

            full = state.prefix + (leaf,)
            yield self._spec.assemble(full)
            produced += 1
            last_idx = idx

