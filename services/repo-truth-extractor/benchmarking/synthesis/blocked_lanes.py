from __future__ import annotations

from typing import Any


def build_blocked_lane_rows(
    *,
    runtime_route_payload: dict[str, Any],
    pricing_report: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bounded = runtime_route_payload.get("bounded_admissibility_result", {})
    if str(bounded.get("status")) != "admissible":
        rows.append(
            {
                "lane_key": "runtime_route",
                "lane_type": "runtime_route",
                "status": "blocked_lane",
                "reason_codes": list(bounded.get("blocking_reason_codes", [])),
                "notes": list(bounded.get("notes", [])),
                "evidence_refs": ["bounded_admissibility_result"],
            }
        )
    for row in pricing_report.get("rows", []):
        status = str(row.get("pricing_status") or "UNPRICED_UNKNOWN")
        if status in {"UNPRICED_UNKNOWN", "STALE_NEEDS_REFRESH"}:
            rows.append(
                {
                    "lane_key": str(row["model_key"]),
                    "lane_type": "pricing_support",
                    "status": "blocked_lane",
                    "reason_codes": [status],
                    "notes": ["Pricing truth is insufficient for cost-optimized synthesis."],
                    "evidence_refs": ["pricing_coverage_report.json"],
                }
            )
    return rows
