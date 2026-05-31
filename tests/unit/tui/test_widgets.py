"""Unit tests for TUI panel widgets."""

from __future__ import annotations

from unittest.mock import patch
import pytest
from rich.panel import Panel

from dopemux.tui.widgets.today import TodayPanel
from dopemux.tui.widgets.authority import AuthorityPanel
from dopemux.tui.widgets.packets import PacketsPanel
from dopemux.tui.widgets.proof import ProofPanel
from dopemux.tui.widgets.risks import RisksPanel
from dopemux.tui.widgets.pr_queue import PRQueuePanel
from dopemux.tui.widgets.context import ContextPanel
from dopemux.tui.widgets.do_not_touch import DoNotTouchPanel


class TestTUIWidgets:
    @pytest.fixture(autouse=True)
    def mock_ui_data_sources(self, monkeypatch):
        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.build_pr_queue",
            lambda *args, **kwargs: {"kind": "pr_queue", "entries": []}
        )
        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.context_status",
            lambda *args, **kwargs: {"dope-context": {"fresh": True}}
        )

    def test_today_panel_render(self):
        panel = TodayPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "DAILY MATRIX" in str(res.title)

    def test_authority_panel_render(self):
        panel = AuthorityPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "INTEGRATION AUTHORITY" in str(res.title)

    def test_packets_panel_render(self):
        panel = PacketsPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "TASK PACKETS" in str(res.title)

    def test_proof_panel_render(self):
        panel = ProofPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "PROOF ATTESTATION" in str(res.title)

    def test_risks_panel_render(self):
        panel = RisksPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "OPEN SECURITY RISKS" in str(res.title)

    def test_pr_queue_panel_render(self):
        panel = PRQueuePanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "PR READINESS" in str(res.title)

    def test_context_panel_render(self):
        panel = ContextPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "CONTEXT FRESHNESS" in str(res.title)

    def test_do_not_touch_panel_render(self):
        panel = DoNotTouchPanel()
        res = panel.render()
        assert isinstance(res, Panel)
        assert "REFUSAL MATRIX" in str(res.title)

    def test_widget_failure_handling(self):
        # Verify that widgets catch exceptions and render failure panels cleanly
        with patch("dopemux.tui.widgets.today.get_panel_data", side_effect=ValueError("Boom")):
            panel = TodayPanel()
            res = panel.render()
            assert isinstance(res, Panel)
            assert "Boom" in str(res.renderable)
