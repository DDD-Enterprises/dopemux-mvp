"""
Unit tests for .claude/hooks/orchestrator_session_start.py
and .claude/hooks/orchestrator_post_edit_nudge.py.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Make .claude/hooks/ importable for these tests.
_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from orchestrator_session_start import (  # noqa: E402
    _CACHE_MAX_AGE_HOURS,
    emit_session_context,
    read_context_cache,
    short_id,
    write_context_cache,
)
from orchestrator_post_edit_nudge import (  # noqa: E402
    EDIT_THRESHOLD,
    NUDGE_COOLDOWN,
    _nudge_path,
    on_edit_tool,
    reset_edit_counter,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cache(tmp_path: Path, *, age_hours: float = 0, extra: dict | None = None) -> Path:
    """Write a valid context cache file and return its path."""
    written_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    data: dict = {
        "written_at": written_at.isoformat(),
        "activeItems": [],
        "blockedItems": [],
        "stalledItems": [],
    }
    if extra:
        data.update(extra)
    cache_path = tmp_path / ".claude" / ".orchestrator-context-cache.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data))
    return cache_path


# ---------------------------------------------------------------------------
# short_id
# ---------------------------------------------------------------------------

def test_short_id_returns_first_8_chars():
    assert short_id("abcd1234-5678-0000") == "abcd1234"


def test_short_id_empty_string():
    assert short_id("") == "?"


# ---------------------------------------------------------------------------
# read_context_cache
# ---------------------------------------------------------------------------

def test_read_context_cache_missing_file(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    assert read_context_cache(tmp_path) is None


def test_read_context_cache_fresh(tmp_path):
    _make_cache(tmp_path, age_hours=0)
    result = read_context_cache(tmp_path)
    assert result is not None
    assert "activeItems" in result


def test_read_context_cache_stale(tmp_path):
    _make_cache(tmp_path, age_hours=_CACHE_MAX_AGE_HOURS + 0.1)
    assert read_context_cache(tmp_path) is None


def test_read_context_cache_just_past_limit_is_stale(tmp_path):
    _make_cache(tmp_path, age_hours=_CACHE_MAX_AGE_HOURS + 0.01)
    assert read_context_cache(tmp_path) is None


def test_read_context_cache_malformed_json(tmp_path):
    path = tmp_path / ".claude" / ".orchestrator-context-cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json {{{")
    assert read_context_cache(tmp_path) is None


def test_read_context_cache_missing_written_at(tmp_path):
    """Cache without written_at is returned as-is (no TTL check possible)."""
    path = tmp_path / ".claude" / ".orchestrator-context-cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"activeItems": [{"id": "abc"}]}))
    result = read_context_cache(tmp_path)
    assert result is not None
    assert result["activeItems"][0]["id"] == "abc"


# ---------------------------------------------------------------------------
# write_context_cache
# ---------------------------------------------------------------------------

def test_write_context_cache_from_dict(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    payload = {"activeItems": [{"id": "x1", "role": "work"}]}
    write_context_cache(tmp_path, payload)
    result = read_context_cache(tmp_path)
    assert result is not None
    assert result["activeItems"][0]["id"] == "x1"


def test_write_context_cache_from_json_string(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"activeItems": [{"id": "x2", "role": "work"}]})
    write_context_cache(tmp_path, payload)
    result = read_context_cache(tmp_path)
    assert result is not None
    assert result["activeItems"][0]["id"] == "x2"


def test_write_context_cache_ignores_unsupported_type(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    write_context_cache(tmp_path, 12345)
    assert read_context_cache(tmp_path) is None


def test_write_context_cache_stamps_written_at(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    write_context_cache(tmp_path, {"activeItems": []})
    result = read_context_cache(tmp_path)
    assert result is not None
    assert "written_at" in result


# ---------------------------------------------------------------------------
# emit_session_context
# ---------------------------------------------------------------------------

def test_emit_session_context_no_cache(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    assert emit_session_context(tmp_path) is None


def test_emit_session_context_empty_items(tmp_path):
    _make_cache(tmp_path)
    assert emit_session_context(tmp_path) is None


def test_emit_session_context_with_active_items(tmp_path):
    _make_cache(
        tmp_path,
        extra={
            "activeItems": [{"id": "abc12345-0000", "title": "My Task", "role": "work"}]
        },
    )
    result = emit_session_context(tmp_path)
    assert result is not None
    assert "abc12345" in result
    assert "My Task" in result


def test_emit_session_context_caps_at_3_active(tmp_path):
    items = [{"id": f"id{i:08d}", "title": f"Task {i}", "role": "work"} for i in range(5)]
    _make_cache(tmp_path, extra={"activeItems": items})
    result = emit_session_context(tmp_path)
    assert result is not None
    assert "… 2 more active item(s)" in result


def test_emit_session_context_title_truncated(tmp_path):
    long_title = "A" * 60
    _make_cache(
        tmp_path,
        extra={"activeItems": [{"id": "abc12345-0000", "title": long_title, "role": "work"}]},
    )
    result = emit_session_context(tmp_path)
    assert result is not None
    assert "…" in result
    # Title is truncated to 54 chars + ellipsis (55 char limit)
    for line in result.splitlines():
        if "AAAA" in line:
            # Extract the title portion between "] " and "  ("
            start = line.index("] ") + 2
            end = line.index("  (")
            title_part = line[start:end]
            assert title_part == "A" * 54 + "…"


def test_emit_session_context_blocked_and_stalled(tmp_path):
    _make_cache(
        tmp_path,
        extra={
            "activeItems": [{"id": "abc12345", "title": "T", "role": "work"}],
            "blockedItems": [{"id": "b1"}, {"id": "b2"}],
            "stalledItems": [{"id": "s1"}],
        },
    )
    result = emit_session_context(tmp_path)
    assert result is not None
    assert "2 blocked" in result
    assert "1 stalled" in result


# ---------------------------------------------------------------------------
# reset_edit_counter
# ---------------------------------------------------------------------------

def test_reset_edit_counter_creates_file(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    reset_edit_counter(tmp_path)
    path = _nudge_path(tmp_path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["edits_since_last_nudge"] == 0


def test_reset_edit_counter_with_session_id(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    reset_edit_counter(tmp_path, session_id="ses-abc123")
    path = _nudge_path(tmp_path, session_id="ses-abc123")
    assert path.exists()
    assert "ses-abc1" in path.name


def test_reset_edit_counter_different_sessions_independent(tmp_path):
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    reset_edit_counter(tmp_path, session_id="aaaaaaaa-session-1")
    reset_edit_counter(tmp_path, session_id="bbbbbbbb-session-2")
    path_a = _nudge_path(tmp_path, session_id="aaaaaaaa-session-1")
    path_b = _nudge_path(tmp_path, session_id="bbbbbbbb-session-2")
    assert path_a != path_b
    assert path_a.exists()
    assert path_b.exists()


# ---------------------------------------------------------------------------
# on_edit_tool  (threshold / cooldown transitions)
# ---------------------------------------------------------------------------

def _write_cache_with_work_item(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    _make_cache(
        tmp_path,
        extra={"activeItems": [{"id": "work-item-uuid", "title": "My Work", "role": "work"}]},
    )


def test_on_edit_tool_no_work_item_returns_none(tmp_path):
    _make_cache(tmp_path, extra={"activeItems": []})
    assert on_edit_tool(tmp_path) is None


def test_on_edit_tool_below_threshold_returns_none(tmp_path):
    _write_cache_with_work_item(tmp_path)
    reset_edit_counter(tmp_path)
    for _ in range(EDIT_THRESHOLD - 1):
        result = on_edit_tool(tmp_path)
        assert result is None


def test_on_edit_tool_at_threshold_returns_nudge(tmp_path):
    _write_cache_with_work_item(tmp_path)
    reset_edit_counter(tmp_path)
    result = None
    for _ in range(EDIT_THRESHOLD):
        result = on_edit_tool(tmp_path)
    assert result is not None
    assert "implementation-evidence" in result
    assert "work-item-uuid" in result


def test_on_edit_tool_resets_counter_after_nudge(tmp_path):
    _write_cache_with_work_item(tmp_path)
    reset_edit_counter(tmp_path)
    for _ in range(EDIT_THRESHOLD):
        on_edit_tool(tmp_path)
    # After nudge, counter resets; next nudge at NUDGE_COOLDOWN edits
    for _ in range(NUDGE_COOLDOWN - 1):
        result = on_edit_tool(tmp_path)
        assert result is None


def test_on_edit_tool_cooldown_fires_second_nudge(tmp_path):
    _write_cache_with_work_item(tmp_path)
    reset_edit_counter(tmp_path)
    for _ in range(EDIT_THRESHOLD):
        on_edit_tool(tmp_path)
    result = None
    for _ in range(NUDGE_COOLDOWN):
        result = on_edit_tool(tmp_path)
    assert result is not None
    assert "implementation-evidence" in result


def test_on_edit_tool_session_scoped_counters_independent(tmp_path):
    """Two session IDs must have independent counters."""
    _write_cache_with_work_item(tmp_path)
    reset_edit_counter(tmp_path, session_id="aaaaaaaa-S1")
    reset_edit_counter(tmp_path, session_id="bbbbbbbb-S2")

    # Drive session S1 to threshold
    result_s1 = None
    for _ in range(EDIT_THRESHOLD):
        result_s1 = on_edit_tool(tmp_path, session_id="aaaaaaaa-S1")

    # S2 should still be below threshold
    result_s2 = on_edit_tool(tmp_path, session_id="bbbbbbbb-S2")

    assert result_s1 is not None
    assert result_s2 is None
