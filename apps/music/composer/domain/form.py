from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class Section:
    """曲式段落（A/B/C/Bridge 等）与其结构信息。"""

    label: str
    length: int
    role: Optional[str] = None
    key_ref: Optional[str] = None
    mode_ref: Optional[str] = None


@dataclass
class Form:
    """曲式对象：由若干段落组成，可带重复与边界信息。"""

    sections: List[Section] = field(default_factory=list)
    repeats: List[Tuple[int, int]] = field(default_factory=list)

    def total_length(self) -> int:
        return sum(sec.length for sec in self.sections)
