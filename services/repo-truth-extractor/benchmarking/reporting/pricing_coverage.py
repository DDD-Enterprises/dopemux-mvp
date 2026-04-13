from __future__ import annotations

from typing import Any

from ..pricing.coverage import build_pricing_coverage_report


def build_pricing_coverage_artifacts() -> dict[str, Any]:
    report = build_pricing_coverage_report()
    return {
        "pricing_coverage_report": report,
        "priced_candidate_matrix": report["rows"],
        "pricing_gap_list": [
            row for row in report["rows"] if row["coverage_class"] in {"unknown", "stale", "partially_priced"}
        ],
        "pricing_source_audit": [
            {
                "model_key": row["model_key"],
                "pricing_source_type": row["pricing_source_type"],
                "pricing_source_ref": row["pricing_source_ref"],
                "pricing_status": row["pricing_status"],
                "pricing_confidence": row["pricing_confidence"],
            }
            for row in report["rows"]
        ],
    }
