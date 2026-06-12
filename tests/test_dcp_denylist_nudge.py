"""
Tests for .claude/hooks/dcp_denylist_nudge.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import dcp_denylist_nudge  # noqa: E402
from dcp_denylist_nudge import _is_facade_adapter, on_facade_edit  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
_FACADE_SRC = "services/dcp-readonly-facade/src/dcp_facade"


def _fake_tokens(tokens: tuple[str, ...]):
    """Patch _denied_tokens to return a fixed set."""
    return patch.object(dcp_denylist_nudge, "_denied_tokens", return_value=tokens)


# ---------------------------------------------------------------------------
# _is_facade_adapter path filtering
# ---------------------------------------------------------------------------

def test_adapter_file_is_detected():
    fp = str(_ROOT / _FACADE_SRC / "conport.py")
    assert _is_facade_adapter(fp, _ROOT) is True


def test_route_manifest_excluded():
    fp = str(_ROOT / _FACADE_SRC / "route_manifest.py")
    assert _is_facade_adapter(fp, _ROOT) is False


def test_tests_dir_excluded():
    fp = str(_ROOT / "services/dcp-readonly-facade/tests/test_route_denylist.py")
    assert _is_facade_adapter(fp, _ROOT) is False


def test_non_facade_path_excluded():
    fp = str(_ROOT / "src/dopemux/cli.py")
    assert _is_facade_adapter(fp, _ROOT) is False


# ---------------------------------------------------------------------------
# on_facade_edit — advisory generation
# ---------------------------------------------------------------------------

def test_denied_token_in_adapter_emits_advisory(tmp_path):
    """Planting memory_store in a fake adapter triggers advisory."""
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "conport.py"
    adapter.write_text("def call():\n    memory_store(data)\n    return result\n")

    with _fake_tokens(("memory_store",)):
        result = on_facade_edit(tmp_path, str(adapter), "sess-1")

    assert result is not None
    assert "memory_store" in result
    assert "L2" in result
    assert "/dcp:denylist-check" in result


def test_token_in_route_manifest_no_advisory(tmp_path):
    """Token in route_manifest.py → None (denylist data itself)."""
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    manifest = facade_dir / "route_manifest.py"
    manifest.write_text('DENIED_TOKENS = ("memory_store",)\n')

    with _fake_tokens(("memory_store",)):
        result = on_facade_edit(tmp_path, str(manifest), "sess-2")

    assert result is None


def test_token_in_tests_no_advisory(tmp_path):
    """Token in tests/ → None (assertions are acceptable)."""
    tests_dir = tmp_path / "services/dcp-readonly-facade/tests"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_route_denylist.py"
    test_file.write_text("assert memory_store not in route\n")

    with _fake_tokens(("memory_store",)):
        result = on_facade_edit(tmp_path, str(test_file), "sess-3")

    assert result is None


def test_clean_adapter_no_advisory(tmp_path):
    """Adapter with no denied tokens → None."""
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "task_orchestrator.py"
    adapter.write_text("def fetch(): return requests.get(url)\n")

    with _fake_tokens(("memory_store", "memory_correct")):
        result = on_facade_edit(tmp_path, str(adapter), "sess-4")

    assert result is None


def test_tokens_load_failure_returns_none(tmp_path):
    """Empty token list (import failure) → None, no exception."""
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "conport.py"
    adapter.write_text("memory_store(data)\n")

    with _fake_tokens(()):
        result = on_facade_edit(tmp_path, str(adapter), "sess-5")

    assert result is None


def test_file_read_error_returns_none(tmp_path):
    """File that can't be read → None, no exception."""
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "conport.py"
    # Don't create the file

    with _fake_tokens(("memory_store",)):
        result = on_facade_edit(tmp_path, str(adapter), "sess-6")

    assert result is None


def test_exception_returns_none(tmp_path):
    """Unexpected exception → None."""
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "conport.py"
    adapter.write_text("memory_store(data)\n")

    with patch.object(dcp_denylist_nudge, "_is_facade_adapter", side_effect=Exception("boom")):
        result = on_facade_edit(tmp_path, str(adapter), "sess-7")

    assert result is None


# ---------------------------------------------------------------------------
# Cooldown
# ---------------------------------------------------------------------------

def test_cooldown_same_session(tmp_path):
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "conport.py"
    adapter.write_text("memory_store(data)\n")

    with _fake_tokens(("memory_store",)):
        first = on_facade_edit(tmp_path, str(adapter), "sess-A")
    assert first is not None

    with _fake_tokens(("memory_store",)):
        second = on_facade_edit(tmp_path, str(adapter), "sess-A")
    assert second is None


def test_cooldown_different_session(tmp_path):
    facade_dir = tmp_path / _FACADE_SRC
    facade_dir.mkdir(parents=True)
    adapter = facade_dir / "conport.py"
    adapter.write_text("memory_store(data)\n")

    with _fake_tokens(("memory_store",)):
        first = on_facade_edit(tmp_path, str(adapter), "sess-A")
    assert first is not None

    with _fake_tokens(("memory_store",)):
        second = on_facade_edit(tmp_path, str(adapter), "sess-B")
    assert second is not None


# ---------------------------------------------------------------------------
# Live token load (integration — skipped if facade not present)
# ---------------------------------------------------------------------------

def test_live_tokens_load_from_route_manifest():
    """Verify DENIED_TOKENS can actually be loaded from the real route_manifest."""
    import dcp_denylist_nudge as m
    m._denied_tokens_cache = None  # reset module cache

    tokens = dcp_denylist_nudge._denied_tokens(_ROOT)
    # If the facade exists, we should get a non-empty tuple
    manifest = _ROOT / _FACADE_SRC / "route_manifest.py"
    if manifest.exists():
        assert len(tokens) > 0, "Expected DENIED_TOKENS to be non-empty from live manifest"
    else:
        assert tokens == (), "Expected () when manifest not present"
