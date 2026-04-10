from __future__ import annotations

from .base import ValidationResult, ValidatorWrapper


class FLIntValidatorWrapper(ValidatorWrapper):
    wrapper_name = "fl_int_validator"

    def validate(self, execution_result, case: dict[str, Any]) -> ValidationResult:
        payload = execution_result.outputs.get("FL_INT_MACHINE_SUMMARY.json")
        passed = isinstance(payload, dict) and str(payload.get("status")) in {"DRY_RUN", "OK"}
        return ValidationResult(
            wrapper_name=self.wrapper_name,
            validator_suite_id=str(case["validator_suite_id"]),
            strength_class="strong",
            passed=passed,
            failure_reason=None if passed else "fl_int_summary_invalid",
            details_payload=payload if isinstance(payload, dict) else {"payload_missing": True},
        )

