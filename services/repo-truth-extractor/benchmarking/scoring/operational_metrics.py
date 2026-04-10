from __future__ import annotations

from typing import Any

from .contract_gate import ContractGateOutcome


def normalize_operational_metrics(
    attempt: dict[str, Any],
    route_trace: dict[str, Any],
    task_eval: dict[str, Any],
    contract_gate: ContractGateOutcome,
) -> dict[str, float | int]:
    route_hops = route_trace.get("route_hops")
    if isinstance(route_hops, list):
        route_hop_total = len(route_hops)
    else:
        route_hop_total = int(attempt.get("route_hop_total", 0))
    latency_ms = float(task_eval.get("latency_ms", attempt.get("operational_metrics", {}).get("latency_ms", 0.0)))  # type: ignore[union-attr]
    tokens_input = int(task_eval.get("tokens_input", attempt.get("operational_metrics", {}).get("tokens_input", 0)))  # type: ignore[union-attr]
    tokens_output = int(task_eval.get("tokens_output", attempt.get("operational_metrics", {}).get("tokens_output", 0)))  # type: ignore[union-attr]
    cost_estimate = float(task_eval.get("cost_estimate_usd", attempt.get("operational_metrics", {}).get("cost_estimate_usd", 0.0)))  # type: ignore[union-attr]
    repair_invocations = int(attempt.get("repair_invocations", 0))
    sidefill_invocations = int(attempt.get("sidefill_invocations", 0))
    stability_score = 1.0
    if repair_invocations or sidefill_invocations:
        stability_score = max(0.0, 1.0 - ((repair_invocations + sidefill_invocations) * 0.15))
    if not contract_gate.first_pass_valid:
        stability_score = round(stability_score * 0.9, 6)
    return {
        "latency_ms": latency_ms,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "cost_estimate_usd": round(cost_estimate, 6),
        "route_hop_total": route_hop_total,
        "repair_invocations": repair_invocations,
        "sidefill_invocations": sidefill_invocations,
        "request_error_rate": 0.0 if contract_gate.contract_gate_pass else 1.0,
        "stability_score": round(stability_score, 6),
        "first_pass_valid": 1 if contract_gate.first_pass_valid else 0,
    }
