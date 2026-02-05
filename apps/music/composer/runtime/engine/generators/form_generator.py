# Generator module for form generator
from typing import List


class FormGenerator:
    def __init__(self, candidates: List[object] | None = None):
        self.candidates = candidates

    def propose(self) -> List[object]:
        return list(self.candidates or [])
