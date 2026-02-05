# Module for interfaces
from typing import Any


class Strategy:
    def build(self, style) -> Any:
        raise NotImplementedError
