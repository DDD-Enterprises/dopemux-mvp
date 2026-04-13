from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models.entities import ControlDelta
from ..models.ids import synthetic_id
from ..policies.loader import load_policy_pack
from ..storage.hashing import hash_json


_POLICY = load_policy_pack("control_anchor_policy_v1.json")
COMPARISON_FIELDS = tuple(str(value) for value in _POLICY["comparison_fields"])


@dataclass(frozen=True)
class ControlDeltaOutcome:
    rows: list[ControlDelta]
    comparable: bool
    anchor_attempt_id: str
    reason: str | None = None


def comparable_attempts(candidate: dict[str, Any], anchor: dict[str, Any]) -> bool:
    return all(candidate.get(field) == anchor.get(field) for field in COMPARISON_FIELDS)


def compute_control_deltas(candidate: dict[str, Any], anchor: dict[str, Any]) -> ControlDeltaOutcome:
    comparable = comparable_attempts(candidate, anchor)
    state = "computed" if comparable else "not_comparable"
    reason = None if comparable else "comparison_key_mismatch"
    metrics = {
        "contract_pass": (1.0 if candidate.get("contract_gate_pass") else 0.0, 1.0 if anchor.get("contract_gate_pass") else 0.0),
        "task_success": (float(candidate.get("task_success_score", 0.0)), float(anchor.get("task_success_score", 0.0))),
        "latency_ms": (
            float(candidate.get("operational_metrics", {}).get("latency_ms", 0.0)),
            float(anchor.get("operational_metrics", {}).get("latency_ms", 0.0)),
        ),
        "cost_estimate_usd": (
            float(candidate.get("operational_metrics", {}).get("cost_estimate_usd", 0.0)),
            float(anchor.get("operational_metrics", {}).get("cost_estimate_usd", 0.0)),
        ),
        "stability_score": (
            float(candidate.get("operational_metrics", {}).get("stability_score", 0.0)),
            float(anchor.get("operational_metrics", {}).get("stability_score", 0.0)),
        ),
    }
    rows: list[ControlDelta] = []
    for metric_name, (candidate_value, anchor_value) in metrics.items():
        delta_value = round(candidate_value - anchor_value, 6) if comparable else 0.0
        rows.append(
            ControlDelta(
                control_delta_id=synthetic_id("control_delta", f"{candidate['case_attempt_id']}_{metric_name}"),
                candidate_attempt_id=str(candidate["case_attempt_id"]),
                anchor_attempt_id=str(anchor["case_attempt_id"]),
                metric_name=metric_name,
                candidate_value=candidate_value,
                anchor_value=anchor_value,
                delta_value=delta_value,
                delta_state=state if reason is None else f"{state}:{reason}",
                content_hash=hash_json(
                    {
                        "candidate_attempt_id": candidate["case_attempt_id"],
                        "anchor_attempt_id": anchor["case_attempt_id"],
                        "metric_name": metric_name,
                        "delta_state": state,
                    }
                ),
                source_ref="m3_control_delta_engine",
                notes=[] if reason is None else [reason],
            )
        )
    return ControlDeltaOutcome(rows=rows, comparable=comparable, anchor_attempt_id=str(anchor["case_attempt_id"]), reason=reason)
