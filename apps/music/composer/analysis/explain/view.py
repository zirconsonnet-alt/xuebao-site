from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Iterable, Iterator, Mapping, Optional, Tuple


class FieldGroup(str, Enum):
    META = "meta"
    ENTITY = "entity"
    EVIDENCE = "evidence"
    ANALYSIS = "analysis"


class FieldSource(str, Enum):
    HIT = "hit"
    ANALYSIS = "analysis"


@dataclass(frozen=True, slots=True)
class FieldSpec:
    key: str
    group: FieldGroup
    title: str
    typ: object
    source: FieldSource
    stable: bool = True
    jsonable: bool = False


@dataclass(frozen=True, slots=True)
class Field:
    spec: FieldSpec
    getter: Callable[[Any], Any]
    serializer: Optional[Callable[[Any], Any]] = None


@dataclass(frozen=True, slots=True)
class FieldError:
    error_type: str
    message: str

    @classmethod
    def from_exc(cls, exc: BaseException) -> "FieldError":
        return cls(error_type=exc.__class__.__name__, message=str(exc))


class AnalysisView(Mapping[str, Any]):
    """
    A self-describing dict-like view for analysis results.

    - Use `schema()` to discover all keys and their metadata (group/title/type/source).
    - Use mapping access (`view[key]`) to retrieve values with lazy evaluation + caching.
    - Use `as_grouped_dict()` / `materialize()` for reporting.
    """

    __slots__ = ("_obj", "_fields", "_by_key", "_cache")

    def __init__(self, obj: Any, fields: Iterable[Field]):
        fs = tuple(fields)
        by_key: Dict[str, Field] = {}
        for f in fs:
            k = f.spec.key
            if k in by_key:
                raise ValueError(f"duplicate analysis view key: {k}")
            by_key[k] = f
        self._obj = obj
        self._fields = fs
        self._by_key = by_key
        self._cache: Dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        if key in self._cache:
            return self._cache[key]
        f = self._by_key[key]
        try:
            value = f.getter(self._obj)
        except Exception as exc:  # noqa: BLE001
            value = FieldError.from_exc(exc)
        self._cache[key] = value
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self._by_key.keys())

    def __len__(self) -> int:
        return len(self._by_key)

    def schema(self) -> Tuple[FieldSpec, ...]:
        return tuple(f.spec for f in self._fields)

    def keys_in(self, group: FieldGroup) -> Tuple[str, ...]:
        return tuple(f.spec.key for f in self._fields if f.spec.group == group)

    def as_grouped_dict(self) -> Dict[FieldGroup, Dict[str, Any]]:
        out: Dict[FieldGroup, Dict[str, Any]] = {g: {} for g in FieldGroup}
        for f in self._fields:
            out[f.spec.group][f.spec.key] = self[f.spec.key]
        return out

    def materialize(self, *, jsonable_only: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for f in self._fields:
            spec = f.spec
            if jsonable_only and not spec.jsonable:
                continue
            value = self[spec.key]
            if jsonable_only and f.serializer is not None and not isinstance(value, FieldError):
                try:
                    value = f.serializer(value)
                except Exception as exc:  # noqa: BLE001
                    value = FieldError.from_exc(exc)
            out[spec.key] = value
        return out
