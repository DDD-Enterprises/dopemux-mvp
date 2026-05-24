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
        # Optimizer fields (additive — May 2026 schema extension).
        # All None-able; consumers fall back to provider defaults.
        "service_tier_flex_multiplier": _decimal_or_none(row.get("service_tier_flex_multiplier")),
        "service_tier_priority_multiplier": _decimal_or_none(row.get("service_tier_priority_multiplier")),
        "cache_read_multiplier": _decimal_or_none(row.get("cache_read_multiplier")),
        "cache_write_5m_multiplier": _decimal_or_none(row.get("cache_write_5m_multiplier")),
        "cache_write_1h_multiplier": _decimal_or_none(row.get("cache_write_1h_multiplier")),
        "prompt_cache_min_tokens": (
            int(row["prompt_cache_min_tokens"])
            if row.get("prompt_cache_min_tokens") is not None
            else None
        ),
        "auto_cache_enabled": (
            bool(row["auto_cache_enabled"])
            if row.get("auto_cache_enabled") is not None
            else None
        ),
        "tiered_input_threshold_tokens": (
            int(row["tiered_input_threshold_tokens"])
            if row.get("tiered_input_threshold_tokens") is not None
            else None
        ),
        "tiered_input_above_cost_per_m": _decimal_or_none(
            row.get("tiered_input_above_cost_per_m")
        ),
        "tiered_output_above_cost_per_m": _decimal_or_none(
            row.get("tiered_output_above_cost_per_m")
        ),
        "tiered_cached_input_above_cost_per_m": _decimal_or_none(
            row.get("tiered_cached_input_above_cost_per_m")
        ),
        "data_residency_us_multiplier": _decimal_or_none(
            row.get("data_residency_us_multiplier")
        ),
        "context_window": (
            int(row["context_window"])
            if row.get("context_window") is not None
            else None
        ),
        "supports_json_schema_strict": (
            bool(row["supports_json_schema_strict"])
            if row.get("supports_json_schema_strict") is not None
            else None
        ),
        "supports_reasoning_toggle": (
            bool(row["supports_reasoning_toggle"])
            if row.get("supports_reasoning_toggle") is not None
            else None
        ),
        "alias_of": str(row["alias_of"]).strip().lower() if row.get("alias_of") else None,
        "specialization": str(row["specialization"]).strip().lower() if row.get("specialization") else None,
    }

    if status in {"PRICED_CONFIRMED", "PRICED_WITH_CAVEAT", "STALE_NEEDS_REFRESH"}:
        if normalized["input_cost_per_m"] is None or normalized["output_cost_per_m"] is None:
            raise RuntimeError(f"Missing rate values for priced entry {model_key}")
    return normalized
