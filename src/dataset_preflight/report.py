"""Serializable validation reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    row: int | None = None
    column: str | None = None
    value: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class ValidationReport:
    contract: str
    source: str
    rows: int
    issues: tuple[Issue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "source": self.source,
            "rows": self.rows,
            "valid": self.valid,
            "issues": [issue.as_dict() for issue in self.issues],
        }
