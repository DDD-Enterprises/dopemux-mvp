from __future__ import annotations

from typing import Any


def classify_spend_truth(
    *,
    measured_spend_usd: float | None,
    expected_spend_usd: float | None,
    pricing_status: str,
) -> str:
    if measured_spend_usd is not None:
        return "measured_spend"
    if pricing_status == "PRICED_CONFIRMED" and expected_spend_usd is not None:
        return "expected_spend"
    if pricing_status in {"PRICED_WITH_CAVEAT", "STALE_NEEDS_REFRESH"} and expected_spend_usd is not None:
        return "partial_estimate"
    if expected_spend_usd is not None:
        return "partial_estimate"
    return "unknown_spend"


def build_spend_truth_summary(
    *,
    model_key: str,
    pricing_status: str,
    measured_spend_usd: float | None,
    expected_spend_usd: float | None,
    pricing_source_ref: str,
) -> dict[str, Any]:
    return {
        "model_key": model_key,
        "pricing_status": pricing_status,
        "pricing_source_ref": pricing_source_ref,
        "measured_spend_usd": measured_spend_usd,
        "expected_spend_usd": expected_spend_usd,
        "spend_truth_class": classify_spend_truth(
            measured_spend_usd=measured_spend_usd,
            expected_spend_usd=expected_spend_usd,
            pricing_status=pricing_status,
        ),
    }
