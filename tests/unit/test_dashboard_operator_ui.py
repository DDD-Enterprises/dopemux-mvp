from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO

from dopemux.ui import service_endpoints
from dopemux.ui.dashboard import ADHDStatePanel
from dopemux.ui.theme import create_console


def test_resolve_dashboard_endpoints_uses_env_authority(monkeypatch) -> None:
    monkeypatch.setenv("DOPEMUX_ADHD_ENGINE_BASE_URL", "http://adhd.example:9123/api/v1")
    monkeypatch.setenv("CONPORT_URL", "http://conport.example:7777/health")
    monkeypatch.setenv("DOPEMUX_SERENA_PORT", "4406")
    monkeypatch.setenv("DOPECON_BRIDGE_URL", "http://bridge.example:3016/kg")
    monkeypatch.setattr(service_endpoints, "_select_port", lambda candidates: candidates[0])

    endpoints = service_endpoints.resolve_dashboard_endpoints()

    assert endpoints["adhd"].base_url == "http://adhd.example:9123"
    assert endpoints["adhd"].source == "DOPEMUX_ADHD_ENGINE_BASE_URL"
    assert endpoints["conport"].base_url == "http://conport.example:7777"
    assert endpoints["conport"].source == "CONPORT_URL"
    assert endpoints["serena"].base_url == "http://localhost:4406"
    assert endpoints["serena"].source == "DOPEMUX_SERENA_PORT"
    assert endpoints["bridge"].base_url == "http://bridge.example:3016"
    assert endpoints["bridge"].source == "DOPECON_BRIDGE_URL"


def test_refresh_age_label_handles_recent_and_stale_samples() -> None:
    assert service_endpoints.refresh_age_label(None) == "never"
    assert service_endpoints.refresh_age_label(datetime.now(timezone.utc)) == "just now"
    older = datetime.now(timezone.utc) - timedelta(minutes=2, seconds=5)
    assert service_endpoints.refresh_age_label(older) == "2m 5s ago"


def test_dashboard_panel_render_shows_endpoint_next_action_when_offline() -> None:
    panel = ADHDStatePanel()
    panel.is_connected = False
    panel.source_label = "DOPEMUX_ADHD_ENGINE_BASE_URL"
    panel.endpoint_label = "http://adhd.example:9123"

    renderable = panel.render()
    buffer = StringIO()
    console = create_console(file=buffer, force_terminal=False, color_system=None, width=160)
    console.print(renderable)
    rendered = buffer.getvalue()

    assert "ADHD Engine disconnected." in rendered
    assert "DOPEMUX_ADHD_ENGINE_BASE_URL" in rendered
    assert "http://adhd.example:9123" in rendered
    assert "Verify the resolved ADHD Engine endpoint or restart the service." in rendered
