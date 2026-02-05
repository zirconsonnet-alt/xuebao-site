# Module for key style
from typing import Any, Dict
from ..profile import StyleProfile


def build_key_strategy(style: StyleProfile) -> Dict[str, Any]:
    """将风格映射为调性生成策略参数。"""
    return style.parameters.get('key', {})
