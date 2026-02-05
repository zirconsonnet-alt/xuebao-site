from .quality import Quality
from ._intern import InternedMeta, FrozenSlotsMixin


class Transition(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("src", "difference", "dst", "__weakref__")

    @classmethod
    def _cache_key(cls, src: Quality, difference: int, dst: Quality):
        return src, int(difference) % 12, dst

    def __init__(self, src: Quality, difference: int, dst: Quality):
        if not isinstance(src, Quality) or not isinstance(dst, Quality):
            raise TypeError("Transition.src/dst 必须为 Quality")
        if not isinstance(difference, int):
            raise TypeError("Transition.difference 必须为 int")
        self.src = src
        self.difference = int(difference) % 12
        self.dst = dst
        self._freeze()

    def __str__(self) -> str:
        return f"{self.src.name}-{self.difference}-{self.dst.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transition):
            return NotImplemented
        return (
            self.src == other.src
            and self.difference == other.difference
            and self.dst == other.dst
        )

    def __hash__(self) -> int:
        return hash((self.src, self.difference, self.dst))
