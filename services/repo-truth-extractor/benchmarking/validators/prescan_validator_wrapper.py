from __future__ import annotations

from typing import Any

from .base import ValidationResult, ValidatorWrapper


class PrescanValidatorWrapper(ValidatorWrapper):
    wrapper_name = "prescan_validator"

    def validate(self, execution_result, case: dict[str, Any]) -> ValidationResult:
        outputs = execution_result.outputs
        manifest = outputs.get("corpus_manifest.json")
        intelligence = outputs.get("prescan_intelligence.json")
        passed = isinstance(manifest, list) and isinstance(intelligence, dict)
        return ValidationResult(
            wrapper_name=self.wrapper_name,
            validator_suite_id=str(case["validator_suite_id"]),
            strength_class="moderate",
            passed=passed,
            failure_reason=None if passed else "missing_prescan_artifacts",
            details_payload={
                "manifest_present": isinstance(manifest, list),
                "intelligence_present": isinstance(intelligence, dict),
            },
        )
