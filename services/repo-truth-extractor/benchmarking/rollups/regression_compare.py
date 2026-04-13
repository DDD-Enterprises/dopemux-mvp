from __future__ import annotations

from typing import Any


def build_regression_comparison(
    current_case_set_rollup: dict[str, Any],
    prior_case_set_rollup: dict[str, Any] | None,
) -> dict[str, Any]:
    if prior_case_set_rollup is None:
        return {
            "comparison_type": "regression_skeleton",
            "status": "no_prior_rollup",
            "current_case_set_id": current_case_set_rollup["case_set_id"],
        }
    return {
        "comparison_type": "regression_skeleton",
        "status": "compared",
        "current_case_set_id": current_case_set_rollup["case_set_id"],
        "prior_case_set_id": prior_case_set_rollup["case_set_id"],
        "contract_pass_rate_delta": round(
            float(current_case_set_rollup.get("contract_pass_rate", 0.0))
            - float(prior_case_set_rollup.get("contract_pass_rate", 0.0)),
            6,
        ),
        "average_task_success_score_delta": round(
            float(current_case_set_rollup.get("average_task_success_score", 0.0))
            - float(prior_case_set_rollup.get("average_task_success_score", 0.0)),
            6,
        ),
    }
