from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.pricing.coverage import build_pricing_coverage_report


def test_coverage_report_distinguishes_priced_partial_unknown_and_stale() -> None:
    report = build_pricing_coverage_report()
    row_by_key = {row["model_key"]: row for row in report["rows"]}

    assert row_by_key["openrouter/openai/gpt-5.4"]["coverage_class"] == "priced"
    assert row_by_key["openrouter/x-ai/grok-4.1-fast"]["coverage_class"] == "partially_priced"
    assert row_by_key["xai/grok-4.20"]["coverage_class"] == "unknown"
    assert row_by_key["xai/grok-4.20-beta-0309-reasoning"]["coverage_class"] == "stale"


def test_coverage_report_tracks_active_universe_size() -> None:
    report = build_pricing_coverage_report()

    assert report["active_benchmark_universe_size"] == len(report["rows"])
    assert report["coverage_counts"]["priced"] >= 1
