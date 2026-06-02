from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from io import StringIO

from dopemux.ui import service_endpoints
from dopemux.ui.dashboard import (
    ADHDStatePanel,
    DEMO_COGNITIVE_HISTORY,
    DEMO_SWITCHES_HISTORY,
    DEMO_VELOCITY_HISTORY,
    TrendsPanel,
)
from dopemux.ui.theme import create_console


def test_resolve_dashboard_endpoints_uses_env_authority(monkeypatch) -> None:
    monkeypatch.setenv(
        "DOPEMUX_ADHD_ENGINE_BASE_URL", "http://adhd.example:9123/api/v1"
    )
    monkeypatch.setenv("CONPORT_URL", "http://conport.example:7777/health")
    monkeypatch.setenv("DOPEMUX_SERENA_PORT", "4406")
    monkeypatch.setenv("DOPECON_BRIDGE_URL", "http://bridge.example:3016/kg")
    monkeypatch.setattr(
        service_endpoints, "_select_port", lambda candidates: candidates[0]
    )

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
    console = create_console(
        file=buffer, force_terminal=False, color_system=None, width=160
    )
    console.print(renderable)
    rendered = buffer.getvalue()

    assert "ADHD Engine disconnected." in rendered
    assert "DOPEMUX_ADHD_ENGINE_BASE_URL" in rendered
    # Rich layout inserts variable spacing before endpoint values.
    assert re.search(r"endpoint=\s*http://adhd\.example:9123", rendered)
    assert (
        "Verify the resolved ADHD Engine endpoint or restart the service." in rendered
    )


def _render_to_text(renderable: object) -> str:
    buffer = StringIO()
    console = create_console(
        file=buffer, force_terminal=False, color_system=None, width=160
    )
    console.print(renderable)
    return buffer.getvalue()


def _sparkline(data: list[float | int]) -> str:
    chars = "▁▂▃▄▅▆▇█"
    mx = max(data) or 1
    return "".join(chars[min(int((v / mx) * 7), 7)] for v in data)


def test_trends_panel_live_defaults_do_not_use_demo_histories() -> None:
    panel = TrendsPanel()

    assert panel.cognitive_history == []
    assert panel.velocity_history == []
    assert panel.switches_history == []

    rendered = _render_to_text(panel.render())

    assert "UNAVAILABLE" in rendered
    assert "no live trend data" in rendered
    assert _sparkline(DEMO_COGNITIVE_HISTORY) not in rendered
    assert _sparkline(DEMO_VELOCITY_HISTORY) not in rendered
    assert _sparkline(DEMO_SWITCHES_HISTORY) not in rendered


def test_trends_panel_demo_histories_are_explicit() -> None:
    panel = TrendsPanel()

    panel.apply_demo_trends()

    assert panel.cognitive_history == DEMO_COGNITIVE_HISTORY
    assert panel.velocity_history == DEMO_VELOCITY_HISTORY
    assert panel.switches_history == DEMO_SWITCHES_HISTORY

    rendered = _render_to_text(panel.render())

    assert _sparkline(DEMO_COGNITIVE_HISTORY) in rendered
    assert _sparkline(DEMO_VELOCITY_HISTORY) in rendered
    assert _sparkline(DEMO_SWITCHES_HISTORY) in rendered


def test_resolve_dashboard_endpoints_ignores_invalid_explicit_url(monkeypatch) -> None:
    monkeypatch.setenv(
        "DOPEMUX_ADHD_ENGINE_BASE_URL",
        "http://adhd.example:notaport/api/v1",
    )
    monkeypatch.delenv("DOPEMUX_ADHD_ENGINE_PORT", raising=False)
    monkeypatch.setattr(
        service_endpoints, "_select_port", lambda candidates: candidates[0]
    )

    endpoint = service_endpoints.resolve_adhd_engine_endpoint()

    assert endpoint.base_url == "http://localhost:5448"
    assert endpoint.source == "default:5448"
