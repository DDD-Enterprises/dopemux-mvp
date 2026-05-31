"""Unit and integration tests for the TUI application shell."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from click.testing import CliRunner

from dopemux.cli import cli
from dopemux.tui.app import OrchestratorTUI


class TestTUIApp:
    @pytest.fixture(autouse=True)
    def mock_ui_data_sources(self, monkeypatch):
        # Prevent any live adapter or network call during TUI boot tests
        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.build_pr_queue",
            lambda *args, **kwargs: {"kind": "pr_queue", "entries": []}
        )
        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.context_status",
            lambda *args, **kwargs: {"dope-context": {"fresh": True}}
        )

    @pytest.mark.asyncio
    async def test_app_telemetry_layout(self):
        app = OrchestratorTUI(once=True)
        assert app.once is True
        async with app.run_test() as pilot:
            assert pilot.app.query_one("#tui-today") is not None
            assert pilot.app.query_one("#tui-authority") is not None
            assert pilot.app.query_one("#tui-packets") is not None

    @pytest.mark.asyncio
    async def test_app_once_headless_run(self):
        app = OrchestratorTUI(once=True)
        async with app.run_test() as pilot:
            # Headless run should exit cleanly without exceptions
            assert pilot.app.once is True

    def test_cli_tui_command_once(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["orchestrator", "tui", "--once"])
        assert result.exit_code == 0
