from __future__ import annotations

from decimal import Decimal
from typing import Any


ALLOWED_PRICING_STATUS = {
    "PRICED_CONFIRMED",
    "PRICED_WITH_CAVEAT",
    "UNPRICED_UNKNOWN",
    "STALE_NEEDS_REFRESH",
    "NOT_APPLICABLE",
}
ALLOWED_PRICING_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    token = str(value).strip()
    if not token:
        return None
    return Decimal(token)


def normalize_pricing_entry(model_key: str, row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise RuntimeError(f"Pricing entry must be an object for {model_key}")

    status = str(row.get("pricing_status") or "UNPRICED_UNKNOWN").strip().upper()
    if status not in ALLOWED_PRICING_STATUS:
        raise RuntimeError(f"Invalid pricing_status for {model_key}: {status}")

    confidence = str(row.get("pricing_confidence") or "UNKNOWN").strip().upper()
    if confidence not in ALLOWED_PRICING_CONFIDENCE:
        raise RuntimeError(f"Invalid pricing_confidence for {model_key}: {confidence}")

    normalized = {
        "model_key": str(model_key).strip().lower(),
        "pricing_source_type": str(row.get("pricing_source_type") or "unknown"),
        "pricing_source_ref": str(row.get("pricing_source_ref") or ""),
        "pricing_confidence": confidence,
        "pricing_currency": str(row.get("pricing_currency") or "USD"),
        "input_unit_cost": _decimal_or_none(row.get("input_unit_cost")),
        "output_unit_cost": _decimal_or_none(row.get("output_unit_cost")),
        "cached_input_cost": _decimal_or_none(row.get("cached_input_cost")),
        "reasoning_cost": _decimal_or_none(row.get("reasoning_cost")),
        "batch_discount": _decimal_or_none(row.get("batch_discount")),
        "surface_scope": str(row.get("surface_scope") or "unknown"),
        "effective_start_date": row.get("effective_start_date"),
        "effective_end_date": row.get("effective_end_date"),
        "pricing_status": status,
        "pricing_caveat": str(row.get("pricing_caveat") or ""),
        "input_cost_per_m": _decimal_or_none(row.get("input_cost_per_m")),
        "output_cost_per_m": _decimal_or_none(row.get("output_cost_per_m")),
    }

    if status in {"PRICED_CONFIRMED", "PRICED_WITH_CAVEAT", "STALE_NEEDS_REFRESH"}:
        if normalized["input_cost_per_m"] is None or normalized["output_cost_per_m"] is None:
            raise RuntimeError(f"Missing rate values for priced entry {model_key}")
    return normalized
