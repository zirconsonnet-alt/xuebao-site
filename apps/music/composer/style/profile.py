# Module for profile
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class StyleProfile:
    """风格配置：可序列化的风格参数与偏好。"""

    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
