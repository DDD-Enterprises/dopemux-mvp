from __future__ import annotations

from .base import ValidationResult, ValidatorWrapper


class PhaseSValidatorWrapper(ValidatorWrapper):
    wrapper_name = "phase_s_validator"

    def validate(self, execution_result, case: dict[str, Any]) -> ValidationResult:
        payload = execution_result.outputs.get("phase_s_registry_summary.json")
        passed = isinstance(payload, dict) and int(payload.get("registry_step_count", 0)) > 0
        return ValidationResult(
            wrapper_name=self.wrapper_name,
            validator_suite_id=str(case["validator_suite_id"]),
            strength_class="moderate",
            passed=passed,
            failure_reason=None if passed else "phase_s_registry_empty",
            details_payload=payload if isinstance(payload, dict) else {"payload_missing": True},
        )

