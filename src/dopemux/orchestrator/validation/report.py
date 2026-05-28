"""Deterministic validation report primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


ValidationIssue = Dict[str, str]


def issue(
    code: str,
    message: str,
    *,
    path: str = "",
    severity: str = "error",
) -> ValidationIssue:
    return {
        "code": code,
        "message": message,
        "path": path,
        "severity": severity,
    }


def sort_issues(issues: Iterable[Mapping[str, str]]) -> List[ValidationIssue]:
    return [
        dict(item)
        for item in sorted(
            issues,
            key=lambda row: (
                str(row.get("code", "")),
                str(row.get("path", "")),
                str(row.get("message", "")),
            ),
        )
    ]


@dataclass(frozen=True)
class ValidationReport:
    kind: str
    path: str
    authority: str
    status: str
    valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "authority": self.authority,
            "status": self.status,
            "valid": self.valid,
            "exit_code": self.exit_code,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }


def path_text(path: str | Path) -> str:
    return str(Path(path))
