from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class AuditReport:
    records: List[Dict[str, Any]] = field(default_factory=list)
    base: Optional["AuditReport"] = None

    def add(self, entry: Dict[str, Any]) -> None:
        self.records.append(entry)

    def iter_records(self) -> Iterable[Dict[str, Any]]:
        if self.base is not None:
            yield from self.base.iter_records()
        yield from self.records

