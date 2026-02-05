# Module for defaults
from .interfaces import Strategy


class DefaultStrategy(Strategy):
    def build(self, style):
        return {}
