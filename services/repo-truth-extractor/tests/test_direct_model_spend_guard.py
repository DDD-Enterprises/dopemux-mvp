from __future__ import annotations

import sys
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.direct_model.spend import SpendGuard


def test_spend_guard_flags_unknown_pricing_without_collapsing_truth() -> None:
    guard = SpendGuard()
    estimate = guard.estimate(
        provider="openrouter",
        model_id="x-ai/grok-4.1-fast",
        input_tokens=1000,
        output_tokens=200,
    )
    assert estimate.spend_truth_class in {"catalog_expected", "partial_estimate"}
    payload = guard.record_expected(estimate)
    assert "soft_alert_triggered" in payload


def test_spend_guard_fails_closed_when_projection_exceeds_cap() -> None:
    guard = SpendGuard(hard_cap_usd=0.000001)
    estimate = guard.estimate(
        provider="openrouter",
        model_id="openai/gpt-5.4",
        input_tokens=1000,
        output_tokens=1000,
    )
    with pytest.raises(RuntimeError, match="hard cap"):
        guard.assert_can_afford(estimate)
