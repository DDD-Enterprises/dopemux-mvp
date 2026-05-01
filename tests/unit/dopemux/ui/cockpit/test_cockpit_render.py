"""Architecture-safety contract tests for the PM cockpit render."""

from __future__ import annotations

import pytest

from dopemux.ui.cockpit.render import (
    TOO_SMALL_MESSAGE,
    TOP_LEVEL_MODES,
    PaneDeclaration,
    Top3Block,
    pm_panes,
    render_audit,
    render_pm,
    viewport_supported,
)


# Forbidden phrases per ARCHITECTURE_SAFETY_OVERLAY.md and the slice contract.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "Run History",
    "authority: dopemux",
    "Services authority: dopemux",
    "command authority: dopemux",
    "Bridge actions authority",
    "SRC=dopemux",
    "UNKNOWN→EDGE",
    "UNKNOWN -> EDGE",
    "UNKNOWN=EDGE",
)


# Authority strings that must appear because PM is a split surface.
SPLIT_AUTHORITY_LABELS: tuple[str, ...] = (
    "leantime",
    "task-orchestrator",
    "conport",
    "dope-memory",
    "dope-context",
)


def test_top_level_modes_are_exactly_five_in_order():
    assert TOP_LEVEL_MODES == (
        "PM",
        "Implementer",
        "Overview",
        "Services",
        "Events",
    )


def test_every_pm_pane_has_four_field_declaration():
    panes = pm_panes()
    assert panes, "PM pane list must not be empty"
    for pane in panes:
        decl = pane.declaration
        assert isinstance(decl, PaneDeclaration)
        # All four fields populated, no field is None or empty.
        assert decl.domain
        assert decl.authority
        assert decl.role in {
            "canonical",
            "derived",
            "mirrored",
            "proxied",
            "authoring",
            "chrome",
        }
        assert decl.next_action
        # The four header lines are emitted in canonical order.
        lines = decl.header_lines()
        assert lines[0].startswith("domain: ")
        assert lines[1].startswith("authority: ")
        assert lines[2].startswith("role: ")
        assert lines[3].startswith("next_action: ")


def test_split_authority_labels_present_in_render():
    text = render_pm(cols=120, rows=40).lower()
    for label in SPLIT_AUTHORITY_LABELS:
        assert label in text, f"missing split-authority label: {label}"
    # dopecon-bridge is adapter/proxy only, must appear in proxied context.
    assert "dopecon-bridge" in text
    assert "proxied" in text or "proxy" in text


@pytest.mark.parametrize("size", [(120, 40), (100, 32), (80, 24)])
def test_no_forbidden_phrases_in_any_supported_viewport(size):
    cols, rows = size
    text = render_pm(cols=cols, rows=rows)
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in text, (
            f"forbidden phrase {phrase!r} appeared at {cols}x{rows}"
        )


def test_src_only_appears_on_data_rows_never_on_chrome_rail():
    text = render_pm(cols=120, rows=40)
    lines = text.splitlines()
    chrome_lines = [line for line in lines if line.startswith("[chrome]")]
    assert chrome_lines, "chrome rail must be present"
    for line in chrome_lines:
        assert "SRC=" not in line, f"SRC must not appear on chrome rail: {line!r}"
    # Also: the chrome rail must not claim authority for data.
    for line in chrome_lines:
        assert "authority:" not in line


def test_top3_block_contract_items_more_count_next_token():
    block = Top3Block(
        items=("a", "b", "c", "d"),
        more_count=4,
        next_token="cursor_X",
    )
    rendered = block.to_lines()
    # Top-3 only.
    assert rendered[0] == "  1. a"
    assert rendered[1] == "  2. b"
    assert rendered[2] == "  3. c"
    # more_count + next_token always present.
    assert any(line.strip().startswith("more_count:") for line in rendered)
    assert any(line.strip().startswith("next_token:") for line in rendered)


def test_top3_contract_visible_in_pm_render():
    text = render_pm(cols=120, rows=40)
    assert "more_count:" in text
    assert "next_token:" in text


def test_bridge_collapses_at_80x24():
    text = render_pm(cols=80, rows=24)
    # Bridge segregator pane title must NOT appear at minimum viewport.
    assert "bridge segregator" not in text
    # Bridge MUST be represented as inspector detail only.
    assert "[inspector-detail]" in text
    assert "dopecon-bridge" in text


def test_bridge_pane_present_at_120x40():
    text = render_pm(cols=120, rows=40)
    assert "bridge segregator" in text


def test_below_minimum_viewport_returns_blocker():
    assert render_pm(cols=79, rows=24) == TOO_SMALL_MESSAGE
    assert render_pm(cols=80, rows=23) == TOO_SMALL_MESSAGE
    assert render_pm(cols=40, rows=10) == TOO_SMALL_MESSAGE
    assert TOO_SMALL_MESSAGE.startswith("[BLOCKER]")


def test_viewport_supported_predicate():
    assert viewport_supported(80, 24)
    assert viewport_supported(120, 40)
    assert not viewport_supported(79, 24)
    assert not viewport_supported(80, 23)


def test_render_is_deterministic_across_calls():
    a = render_pm(cols=120, rows=40)
    b = render_pm(cols=120, rows=40)
    assert a == b
    c = render_pm(cols=100, rows=32)
    d = render_pm(cols=100, rows=32)
    assert c == d
    e = render_pm(cols=80, rows=24)
    f = render_pm(cols=80, rows=24)
    assert e == f


def test_render_audit_alias_matches_plain_render():
    assert render_audit(cols=120, rows=40) == render_pm(cols=120, rows=40, plain=True)


def test_static_demo_banner_present():
    text = render_pm(cols=120, rows=40)
    assert "STATIC DEMO" in text
    assert "NO WRITES" in text


def test_top_level_mode_bar_present_in_render():
    text = render_pm(cols=120, rows=40)
    for mode in TOP_LEVEL_MODES:
        assert mode in text
