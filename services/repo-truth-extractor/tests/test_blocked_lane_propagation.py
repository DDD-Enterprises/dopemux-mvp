from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.synthesis.blocked_lanes import build_blocked_lane_rows


def test_blocked_lane_rows_include_runtime_and_pricing_blocks() -> None:
    rows = build_blocked_lane_rows(
        runtime_route_payload={
            "bounded_admissibility_result": {
                "status": "blocked",
                "blocking_reason_codes": ["IDENTICAL_CONTROL_SIGNATURE"],
                "notes": ["R1 restart not truthful."],
            }
        },
        pricing_report={
            "rows": [
                {"model_key": "xai/grok-4.20", "pricing_status": "UNPRICED_UNKNOWN"},
                {"model_key": "xai/grok-4.20-beta-0309-reasoning", "pricing_status": "STALE_NEEDS_REFRESH"},
            ]
        },
    )

    lane_keys = {row["lane_key"] for row in rows}
    assert "runtime_route" in lane_keys
    assert "xai/grok-4.20" in lane_keys
    assert "xai/grok-4.20-beta-0309-reasoning" in lane_keys
