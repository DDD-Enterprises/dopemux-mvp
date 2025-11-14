"""Unit tests for the DØPEMÜX roast engine."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the roast engine service package is importable during tests.
SERVICE_PATH = Path(__file__).resolve().parent.parent / "services" / "roast-engine"
if str(SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(SERVICE_PATH))

from roast_engine import RoastEngine, RoastRequest, SpiceLevel  # noqa: E402


def test_engine_respects_count_and_persona():
    engine = RoastEngine(seed=123)
    request = RoastRequest(user_handle="Tester", count=4, spice_level=SpiceLevel.SFW, seed=99)

    roasts = engine.generate_roasts(request)

    assert len(roasts) == 4
    for roast in roasts:
        assert "Tester" in roast.text
        assert roast.spice_level == SpiceLevel.SFW
        assert roast.status_chip in {"[LIVE]", "[LOGGED]", "[AFTERCARE]"}
        assert "I" in roast.text  # self-roast baked in


def test_context_is_injected():
    engine = RoastEngine(seed=42)
    request = RoastRequest(
        user_handle="Operator X",
        context="fundraising deck",
        count=1,
        spice_level=SpiceLevel.SPICY,
        seed=7,
    )

    roast = engine.generate_roasts(request)[0]

    assert "fundraising deck" in roast.text
    assert roast.register in {"coach_dom", "gremlin_scholar", "aftercare"}


def test_register_bias_is_respected():
    engine = RoastEngine(seed=11)
    request = RoastRequest(
        user_handle="Op",
        count=1,
        spice_level=SpiceLevel.NSFW_EDGE,
        registers=["degradation"],
        seed=3,
    )

    roast = engine.generate_roasts(request)[0]

    assert roast.register == "degradation"
