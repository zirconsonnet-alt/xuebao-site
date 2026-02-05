from threading import RLock
from typing import Any
from weakref import WeakValueDictionary


class InternedMeta(type):
    _global_lock = RLock()

    def __call__(cls, *args: Any, **kwargs: Any):
        key = cls._cache_key(*args, **kwargs)   # type: ignore[attr-defined]
        with InternedMeta._global_lock:
            cache: WeakValueDictionary | None = getattr(cls, "_cache", None)
            if cache is None:
                cache = WeakValueDictionary()
                setattr(cls, "_cache", cache)
            obj = cache.get(key)
            if obj is not None:
                return obj
            obj = super().__call__(*args, **kwargs)
            cache[key] = obj
            return obj


class FrozenSlotsMixin:
    __slots__ = ("_frozen",)

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(f"{type(self).__name__} is immutable")
        super().__setattr__(name, value)

    def _freeze(self) -> None:
        super().__setattr__("_frozen", True)
