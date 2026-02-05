# Module for analyzer
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Analyzer(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    def analyze(self, payload: InputT) -> OutputT: ...
