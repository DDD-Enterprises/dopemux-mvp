from __future__ import annotations

import sys
from pathlib import Path

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.campaigns.route_identity import (
    MALFORMED_ROUTE_TELEMETRY,
    MISSING_ROUTE_TELEMETRY,
    RouteTelemetryError,
    extract_effective_route_signature,
)


def test_extract_effective_route_signature_is_deterministic() -> None:
    signature, signature_hash = extract_effective_route_signature(
        {
            "steps": {
                "A:A2": {"final_route_counts": {"xai/grok-4.20-beta-0309-reasoning": 1}},
                "A:A0": {"final_route_counts": {"openrouter/openai/gpt-5.3-codex": 1}},
            }
        }
    )
    assert signature == {
        "A:A0": ["openrouter/openai/gpt-5.3-codex"],
        "A:A2": ["xai/grok-4.20-beta-0309-reasoning"],
    }
    assert isinstance(signature_hash, str)
    assert len(signature_hash) == 64


def test_extract_effective_route_signature_blocks_missing_steps() -> None:
    with pytest.raises(RouteTelemetryError) as excinfo:
        extract_effective_route_signature({})
    assert excinfo.value.blocker_code == MALFORMED_ROUTE_TELEMETRY


def test_extract_effective_route_signature_blocks_empty_routes() -> None:
    with pytest.raises(RouteTelemetryError) as excinfo:
        extract_effective_route_signature({"steps": {"A:A0": {"final_route_counts": {}}}})
    assert excinfo.value.blocker_code == MISSING_ROUTE_TELEMETRY
