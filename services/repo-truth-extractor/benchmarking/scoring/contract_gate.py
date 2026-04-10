from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models.enums import ContractGateStrength


@dataclass(frozen=True)
class ContractGateOutcome:
    contract_gate_pass: bool
    contract_gate_strength: str
    contract_fail_reason: str | None
    first_pass_valid: bool
    structural_failure_classification: str | None


def _strength_rank(strength: str) -> int:
    ranking = {"weak": 1, "moderate": 2, "strong": 3}
    return ranking.get(strength, 0)


def _classify_failure(
    validator_results: list[dict[str, Any]],
    attempt: dict[str, Any],
    validator_suite: dict[str, Any],
) -> tuple[str, str]:
    failed = [result for result in validator_results if not bool(result.get("passed"))]
    if failed:
        reason = str(failed[0].get("failure_reason") or "validator_failed")
        if "schema" in reason:
            return reason, "strict_schema_violation"
        if "artifact" in reason:
            return reason, "artifact_missing"
        return reason, "validator_failed"
    if not bool(attempt.get("strict_schema_expected", True)):
        return "strict_schema_not_expected", "policy_relaxed"
    rigor = str(validator_suite.get("contract_rigor") or "")
    if "phase_s" in rigor:
        return "phase_s_contract_failure", "phase_s_policy_sensitive"
    return "contract_gate_failed", "structural_contract_failure"


def evaluate_contract_gate(
    attempt: dict[str, Any],
    validator_results: list[dict[str, Any]],
    validator_suite: dict[str, Any],
) -> ContractGateOutcome:
    suite_strength = str(validator_suite.get("strength_class") or attempt.get("contract_gate_strength") or "weak")
    attempt_strength = str(attempt.get("contract_gate_strength") or suite_strength)
    chosen_strength = suite_strength if _strength_rank(suite_strength) >= _strength_rank(attempt_strength) else attempt_strength
    chosen_strength = ContractGateStrength.coerce(chosen_strength).value

    all_passed = bool(validator_results) and all(bool(result.get("passed")) for result in validator_results)
    first_pass_valid = all_passed and int(attempt.get("repair_invocations", 0)) == 0 and int(attempt.get("sidefill_invocations", 0)) == 0
    if all_passed:
        return ContractGateOutcome(
            contract_gate_pass=True,
            contract_gate_strength=chosen_strength,
            contract_fail_reason=None,
            first_pass_valid=first_pass_valid,
            structural_failure_classification=None,
        )
    fail_reason, classification = _classify_failure(validator_results, attempt, validator_suite)
    return ContractGateOutcome(
        contract_gate_pass=False,
        contract_gate_strength=chosen_strength,
        contract_fail_reason=fail_reason,
        first_pass_valid=False,
        structural_failure_classification=classification,
    )
