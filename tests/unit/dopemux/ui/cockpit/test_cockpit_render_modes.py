"""Five-mode Cockpit render facade tests."""

from __future__ import annotations

import pytest

from dopemux.ui.cockpit.render import TOO_SMALL_MESSAGE, render_pm
from dopemux.ui.cockpit.render_modes import (
    SUPPORTED_COCKPIT_MODES,
    normalize_mode,
    render_cockpit,
)


FORBIDDEN_PHRASES: tuple[str, ...] = (
    "Run History",
    "authority: dopemux",
    "Services authority: dopemux",
    "command authority: dopemux",
    "Bridge actions authority",
    "SRC=dopemux",
    "UNKNOWN\u2192EDGE",
    "UNKNOWN -> EDGE",
    "UNKNOWN=EDGE",
    "READY_FOR_CLAUDE_DESIGN: approved",
    "safe_for_claude_design: YES",
)

MODE_AUTHORITY_LABELS: dict[str, tuple[str, ...]] = {
    "pm": ("task-orchestrator", "leantime", "conport"),
    "implementer": ("dopetask", "proof bundle", "task packet"),
    "overview": ("operator control", "runtime code", "bridge proxy"),
    "services": ("service catalog", "typed service-id", "policy gate"),
    "events": ("dope-memory", "event producers", "append-only"),
}


def test_supported_modes_are_exactly_the_electric_refresh_modes():
    assert SUPPORTED_COCKPIT_MODES == (
        "pm",
        "implementer",
        "overview",
        "services",
        "events",
    )


def test_pm_facade_preserves_existing_pm_render_contract():
    assert render_cockpit("pm", cols=120, rows=40, plain=True) == render_pm(
        cols=120,
        rows=40,
        plain=True,
    )


@pytest.mark.parametrize("mode", SUPPORTED_COCKPIT_MODES)
@pytest.mark.parametrize("size", [(120, 40), (100, 32), (80, 24)])
def test_every_supported_mode_renders_deterministic_static_contract(mode, size):
    cols, rows = size
    first = render_cockpit(mode, cols=cols, rows=rows, plain=True)
    second = render_cockpit(mode, cols=cols, rows=rows, plain=True)
    assert first == second
    assert "STATIC DEMO" in first
    assert "NO WRITES" in first
    assert "domain: " in first
    assert "authority: " in first
    assert "role: " in first
    assert "next_action: " in first
    assert "SRC=" in first
    assert "[BLOCKER]" not in first
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in first
    for label in MODE_AUTHORITY_LABELS[mode]:
        assert label in first.lower()


def test_all_modes_share_the_canonical_minimum_viewport_blocker():
    for mode in SUPPORTED_COCKPIT_MODES:
        assert render_cockpit(mode, cols=79, rows=24, plain=True) == TOO_SMALL_MESSAGE
        assert render_cockpit(mode, cols=80, rows=23, plain=True) == TOO_SMALL_MESSAGE


def test_mode_normalization_is_case_insensitive_and_fail_closed():
    assert normalize_mode("PM") == "pm"
    assert normalize_mode("Services") == "services"
    with pytest.raises(ValueError, match="unsupported cockpit mode"):
        normalize_mode("settings")
