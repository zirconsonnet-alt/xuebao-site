# Module for chord style
from typing import Any, Dict
from ..profile import StyleProfile


def build_chord_strategy(style: StyleProfile) -> Dict[str, Any]:
    """将风格映射为和弦生成策略参数。"""
    return style.parameters.get('chord', {})
