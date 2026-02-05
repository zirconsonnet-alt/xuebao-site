# Module for hit
from abc import ABC, abstractmethod
from typing import Iterable, Union
from ...domain.enums.core import Degrees
from ...domain.enums.harmony import Modes
from .kinds import ResolveKind


def format_degrees(degs: Iterable[Degrees]) -> str:
    return "{" + ", ".join(d.name for d in sorted(degs, key=lambda d: d.value)) + "}"


def format_role(role: Union[Modes, Degrees]) -> str:
    return getattr(role, "name", str(role))


class ResolveHit(ABC):
    @property
    @abstractmethod
    def kind(self) -> ResolveKind: ...

    def __str__(self) -> str:
        return f"<{self.kind.name}>"
