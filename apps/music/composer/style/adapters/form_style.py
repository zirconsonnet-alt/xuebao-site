# Module for form style
from typing import Any, Dict
from ..profile import StyleProfile


def build_form_strategy(style: StyleProfile) -> Dict[str, Any]:
    """将风格映射为曲式生成策略参数。"""
    return style.parameters.get('form', {})
