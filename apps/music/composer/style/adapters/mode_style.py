# Module for mode style
from typing import Any, Dict
from ..profile import StyleProfile


def build_mode_strategy(style: StyleProfile) -> Dict[str, Any]:
    """将风格映射为调式生成策略参数。"""
    return style.parameters.get('mode', {})
