from __future__ import annotations

from .base import ValidationResult, ValidatorWrapper


class RuntimeValidatorWrapper(ValidatorWrapper):
    wrapper_name = "runtime_validator"

    def validate(self, execution_result, case: dict[str, Any]) -> ValidationResult:
        qa = execution_result.outputs.get("A0_QA.json")
        qa_merge = execution_result.outputs.get("A99_QA.json")
        dashboard = execution_result.outputs.get("RUN_DASHBOARD.json")
        phase_status = None
        if isinstance(dashboard, dict):
            phase_status = (
                dashboard.get("payload", {})
                .get("phases", {})
                .get("A", {})
                .get("status")
            )
        passed = (
            isinstance(qa, dict)
            and not qa.get("missing_expected_artifacts")
            and isinstance(qa_merge, dict)
            and not qa_merge.get("missing_expected_artifacts")
            and phase_status in {None, "PASS"}
        )
        return ValidationResult(
            wrapper_name=self.wrapper_name,
            validator_suite_id=str(case["validator_suite_id"]),
            strength_class="strong",
            passed=passed,
            failure_reason=None if passed else "missing_expected_artifacts",
            details_payload={
                "a0_qa": qa if isinstance(qa, dict) else {"qa_missing": True},
                "a99_qa": qa_merge if isinstance(qa_merge, dict) else {"qa_missing": True},
                "phase_status": phase_status,
            },
        )
