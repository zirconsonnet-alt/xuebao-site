from enum import Enum
from typing import Any, TypeVar, Type


T = TypeVar("T", bound="LookupEnum")


class LookupEnum(Enum):
    @classmethod
    def get(cls: Type[T], value: Any) -> T:
        try:
            return cls(value)
        except ValueError as e:
            raise ValueError(f"{value!r} is not a valid {cls.__name__}") from e
