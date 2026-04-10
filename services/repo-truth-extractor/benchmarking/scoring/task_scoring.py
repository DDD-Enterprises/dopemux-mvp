from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .archetype_policies import ArchetypePolicy, policy_for_archetype
from .contract_gate import ContractGateOutcome


@dataclass(frozen=True)
class TaskScoreOutcome:
    task_success_score: float
    task_score_breakdown: dict[str, float]
    scoring_policy_id: str
    scoring_policy_version: str


def _presence_score(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (list, tuple, dict, str)):
        return 1.0 if len(value) > 0 else 0.0
    return 1.0


def _dimension_scores(
    policy: ArchetypePolicy,
    attempt: dict[str, Any],
    route_trace: dict[str, Any],
    task_eval: dict[str, Any],
    validator_results: list[dict[str, Any]],
    executor_links: dict[str, Any],
) -> dict[str, float]:
    dimensions: dict[str, float] = {}
    for name in policy.dimensions:
        if name == "surface_explicitness":
            dimensions[name] = 1.0 if attempt.get("surface_class") and attempt.get("surface_id") else 0.0
        elif name == "route_trace_completeness":
            dimensions[name] = 1.0 if "execution_mode" in route_trace and "surface_class" in route_trace else 0.0
        elif name == "inventory_capture":
            dimensions[name] = _presence_score(task_eval)
        elif name == "contract_separation":
            dimensions[name] = 1.0 if attempt.get("runtime_version") and attempt.get("contract_version") and attempt.get("runtime_version") != attempt.get("contract_version") else 0.0
        elif name == "artifact_completeness":
            dimensions[name] = 1.0 if attempt.get("output_artifact_ref") and executor_links.get("script") else 0.0
        elif name == "validator_alignment":
            dimensions[name] = 1.0 if validator_results and all(bool(item.get("passed")) for item in validator_results) else 0.0
        elif name == "registry_resolution":
            dimensions[name] = 1.0 if executor_links.get("registry_path") or task_eval.get("status") else 0.0
        elif name == "repair_discipline":
            repair_total = int(attempt.get("repair_invocations", 0)) + int(attempt.get("sidefill_invocations", 0))
            dimensions[name] = 1.0 if repair_total == 0 else max(0.0, 1.0 - (repair_total * 0.25))
        elif name == "contract_caveat_handling":
            dimensions[name] = 1.0 if attempt.get("contract_gate_strength") in {"moderate", "weak"} else 0.8
        elif name == "conflict_visibility":
            dimensions[name] = _presence_score(route_trace.get("route_hops"))
        elif name == "ruling_consistency":
            dimensions[name] = _presence_score(task_eval.get("task_success_score"))
        elif name == "evidence_traceability":
            dimensions[name] = 1.0 if attempt.get("evidence_bundle_id") else 0.0
        elif name == "machine_summary":
            dimensions[name] = 1.0 if str(attempt.get("output_artifact_ref", "")).endswith(".json") else 0.0
        elif name == "artifact_packaging":
            dimensions[name] = 1.0 if executor_links.get("output_root") or executor_links.get("fixture_root") else 0.0
        elif name == "schema_discipline":
            dimensions[name] = 1.0 if bool(attempt.get("strict_schema_expected")) else 0.0
        elif name == "tool_awareness":
            dimensions[name] = 1.0 if executor_links.get("script") else 0.0
        elif name == "repo_reasoning_trace":
            dimensions[name] = 1.0 if route_trace.get("logical_route_id") or route_trace.get("run_root") else 0.0
        elif name == "phase_caveat_capture":
            dimensions[name] = 1.0 if attempt.get("contract_gate_strength") in {"moderate", "weak"} else 0.6
        else:
            dimensions[name] = 0.0
    return dimensions


def score_attempt(
    case: dict[str, Any],
    attempt: dict[str, Any],
    contract_gate: ContractGateOutcome,
    task_eval: dict[str, Any],
    route_trace: dict[str, Any],
    validator_results: list[dict[str, Any]],
    executor_links: dict[str, Any],
) -> TaskScoreOutcome:
    policy = policy_for_archetype(str(case["archetype_id"]))
    if not contract_gate.contract_gate_pass:
        return TaskScoreOutcome(
            task_success_score=0.0,
            task_score_breakdown={"blocked_by_contract_gate": 1.0},
            scoring_policy_id=policy.policy_id,
            scoring_policy_version=policy.policy_version,
        )
    dimensions = _dimension_scores(policy, attempt, route_trace, task_eval, validator_results, executor_links)
    total = 0.0
    for dimension, weight in policy.weights.items():
        total += dimensions.get(dimension, 0.0) * weight
    return TaskScoreOutcome(
        task_success_score=round(total, 6),
        task_score_breakdown=dimensions,
        scoring_policy_id=policy.policy_id,
        scoring_policy_version=policy.policy_version,
    )
