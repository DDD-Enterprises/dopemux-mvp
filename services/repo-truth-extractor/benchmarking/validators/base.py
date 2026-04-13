from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    wrapper_name: str
    validator_suite_id: str
    strength_class: str
    passed: bool
    failure_reason: str | None
    details_payload: dict[str, Any]


class ValidatorWrapper:
    wrapper_name = "base"

    def validate(self, execution_result: Any, case: dict[str, Any]) -> ValidationResult:
        raise NotImplementedError

