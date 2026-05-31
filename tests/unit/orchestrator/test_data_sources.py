import pytest
import sqlite3
import tempfile
from unittest.mock import patch
from filelock import Timeout

from dopemux.orchestrator.ui.data_sources import get_panel_data, get_all_panels


class TestUIDataSources:
    def test_all_panels_present(self):
        data = get_all_panels()
        expected_panels = {"today", "authority", "packets", "proof", "risks", "pr_queue", "context", "do_not_touch"}
        assert set(data.keys()) == expected_panels

    def test_today_panel_success(self):
        data = get_panel_data("today")
        assert "count" in data
        assert data.get("fallback") is False

    @patch("sqlite3.connect")
    def test_today_panel_sqlite_operational_error_fallback(self, mock_connect):
        # Simulate SQLite operational lock error
        mock_connect.side_effect = sqlite3.OperationalError("database is locked")
        
        data = get_panel_data("today")
        assert data.get("fallback") is True
        assert "error" in data
        assert "degraded" in data["status"]

    @patch("filelock.FileLock.acquire")
    def test_context_panel_filelock_timeout_fallback(self, mock_acquire):
        # Simulate FileLock timeout
        mock_acquire.side_effect = Timeout("lock could not be acquired")

        data = get_panel_data("context")
        assert data.get("fallback") is True
        assert "progress_entries_count" in data
        assert "lock contention fallback" in data["status"]

    def test_context_panel_filelock_uses_tempdir(self, monkeypatch, tmp_path):
        captured = {}

        class DummyLock:
            def __init__(self, path, timeout):
                captured["path"] = path
                captured["timeout"] = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.context_status",
            lambda *args, **kwargs: {"dope-context": {"fresh": True}, "ConPort": {"fresh": True}},
        )
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
        monkeypatch.setattr("filelock.FileLock", DummyLock)

        data = get_panel_data("context")

        assert captured["path"] == str(tmp_path / "dopemux-context-panel.lock")
        assert captured["timeout"] == 0.1
        assert data.get("fallback") is False
