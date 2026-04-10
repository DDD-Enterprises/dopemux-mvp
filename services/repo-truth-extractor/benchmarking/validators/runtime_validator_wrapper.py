from __future__ import annotations

from .base import ValidationResult, ValidatorWrapper


class RuntimeValidatorWrapper(ValidatorWrapper):
    wrapper_name = "runtime_validator"

    def validate(self, execution_result, case: dict[str, Any]) -> ValidationResult:
        qa = execution_result.outputs.get("A0_QA.json")
        passed = isinstance(qa, dict) and not qa.get("missing_expected_artifacts")
        return ValidationResult(
            wrapper_name=self.wrapper_name,
            validator_suite_id=str(case["validator_suite_id"]),
            strength_class="strong",
            passed=passed,
            failure_reason=None if passed else "missing_expected_artifacts",
            details_payload=qa if isinstance(qa, dict) else {"qa_missing": True},
        )

