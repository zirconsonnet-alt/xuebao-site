from typing import Tuple
from .enums.core import Intervals
from ._intern import InternedMeta, FrozenSlotsMixin


IntervalProfile = Tuple[Intervals, ...]


class ColorShift(FrozenSlotsMixin, metaclass=InternedMeta):
    __slots__ = ("src", "diff", "dst", "__weakref__")

    @classmethod
    def _cache_key(cls, src: IntervalProfile, diff: int, dst: IntervalProfile):
        return src, int(diff) % 12, dst

    def __init__(self, src: IntervalProfile, diff: int, dst: IntervalProfile):
        self._validate_profile(src, "src")
        self._validate_profile(dst, "dst")
        if not isinstance(diff, int):
            raise TypeError("ColorShift.diff 必须为 int")
        self.src: IntervalProfile = src
        self.diff: int = int(diff) % 12
        self.dst: IntervalProfile = dst
        self._freeze()

    @staticmethod
    def _validate_profile(p: object, name: str) -> None:
        if not isinstance(p, tuple) or len(p) != 7:
            raise TypeError(f"ColorShift.{name} 必须为长度 7 的 Intervals 元组")
        if any(not isinstance(x, Intervals) for x in p):
            raise TypeError(f"ColorShift.{name} 必须全是 Intervals")
        if p[0] != Intervals.P1:
            raise ValueError(f"ColorShift.{name}[0] 必须为 Intervals.P1")

    def __str__(self) -> str:
        return (
            "ColorShift("
            f"src={[iv.name for iv in self.src]}, "
            f"diff={self.diff}, "
            f"dst={[iv.name for iv in self.dst]}"
            ")"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ColorShift):
            return NotImplemented
        return self.src == other.src and self.dst == other.dst and self.diff == other.diff

    def __hash__(self) -> int:
        return hash((self.src, self.diff, self.dst))
