from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.pricing.spend_truth import build_spend_truth_summary, classify_spend_truth


def test_spend_truth_prefers_measured_spend_when_present() -> None:
    assert (
        classify_spend_truth(
            measured_spend_usd=1.25,
            expected_spend_usd=1.0,
            pricing_status="PRICED_CONFIRMED",
        )
        == "measured_spend"
    )


def test_spend_truth_marks_unknown_when_no_measured_or_expected_cost_exists() -> None:
    payload = build_spend_truth_summary(
        model_key="xai/grok-4.20",
        pricing_status="UNPRICED_UNKNOWN",
        measured_spend_usd=None,
        expected_spend_usd=None,
        pricing_source_ref="https://docs.x.ai/developers/models",
    )

    assert payload["spend_truth_class"] == "unknown_spend"
