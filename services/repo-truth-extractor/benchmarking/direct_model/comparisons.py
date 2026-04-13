from __future__ import annotations

from collections import defaultdict
from typing import Any


def summarize_attempts(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    failures: list[dict[str, Any]] = []
    for attempt in attempts:
        model_key = str(attempt["candidate"]["model_key"])
        by_model[model_key].append(attempt)
        if not bool(attempt.get("validator_pass")):
            failures.append(
                {
                    "case_id": attempt["case_id"],
                    "model_key": model_key,
                    "failure_classification": attempt.get("failure_classification"),
                    "failure_reason": attempt.get("failure_reason"),
                    "lane_boundary_note": "direct_model failures are not route/profile truth",
                }
            )

    per_model: dict[str, Any] = {}
    comparison_rows: list[dict[str, Any]] = []
    for model_key, rows in sorted(by_model.items()):
        validator_passes = sum(1 for row in rows if row.get("validator_pass"))
        mean_score = sum(float(row.get("task_success_score", 0.0)) for row in rows) / len(rows)
        mean_latency_ms = sum(float(row.get("latency_ms", 0.0)) for row in rows) / len(rows)
        total_expected_spend = sum(float(row.get("expected_spend_usd", 0.0)) for row in rows)
        unknown_pricing = any(bool(row.get("pricing_unknown")) for row in rows)
        per_model[model_key] = {
            "model_key": model_key,
            "attempt_count": len(rows),
            "validator_pass_count": validator_passes,
            "validator_pass_rate": round(validator_passes / len(rows), 6),
            "mean_task_success_score": round(mean_score, 6),
            "mean_latency_ms": round(mean_latency_ms, 3),
            "total_expected_spend_usd": round(total_expected_spend, 6),
            "pricing_unknown_present": unknown_pricing,
            "lane_boundary_note": (
                "direct_model evidence supports admission, schema survivability, spend, and latency comparisons only"
            ),
        }
        comparison_rows.append(per_model[model_key])

    return {
        "comparison_rows": comparison_rows,
        "per_model": per_model,
        "failures": failures,
        "lane_boundary_note": (
            "DIRECT_MODEL_COMPARISON is lane-distinct and must not be interpreted as runtime_route or profile truth"
        ),
    }
