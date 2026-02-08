"""Contract tests for leantime-bridge REST compatibility endpoints."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from leantime_bridge import http_server as hs


@pytest.mark.asyncio
async def test_execute_tool_uses_method_fallback_on_failure(monkeypatch):
    """`execute_tool` should retry with next JSON-RPC method candidate."""
    calls: list[str] = []

    async def fake_call_api(self, method: str, params=None):
        calls.append(method)
        if len(calls) == 1:
            raise hs.LeantimeBridgeError("first candidate failed")
        return [{"id": 1, "headline": "Test"}]

    monkeypatch.setattr(hs.LeantimeClient, "call_api", fake_call_api)

    result = await hs.execute_tool("list_tickets", {"projectId": 1})

    assert isinstance(result, list)
    assert result[0]["id"] == 1
    assert calls[0] == hs.TOOL_METHOD_CANDIDATES["list_tickets"][0]
    assert calls[1] == hs.TOOL_METHOD_CANDIDATES["list_tickets"][1]


@pytest.mark.asyncio
async def test_execute_tool_stops_fallback_on_setup_required_error(monkeypatch):
    """Terminal setup errors should not fan out across every method candidate."""
    calls: list[str] = []

    async def fake_call_api(self, method: str, params=None):
        calls.append(method)
        raise hs.LeantimeBridgeError(
            "Leantime instance requires initial setup at /install before API calls can succeed"
        )

    monkeypatch.setattr(hs.LeantimeClient, "call_api", fake_call_api)

    with pytest.raises(hs.LeantimeBridgeError, match="requires initial setup"):
        await hs.execute_tool("list_projects", {})

    assert calls == [hs.TOOL_METHOD_CANDIDATES["list_projects"][0]]


def test_api_tools_endpoint_supports_legacy_create_task_alias(monkeypatch):
    """`create_task` alias should normalize to `create_ticket` with mapped args."""
    captured: dict[str, object] = {}

    async def fake_tool_call(client, tool_name: str, arguments: dict):
        captured["tool_name"] = tool_name
        captured["arguments"] = dict(arguments)
        return {"id": 77, "headline": arguments["headline"]}

    monkeypatch.setattr(hs, "_call_tool_with_method_fallback", fake_tool_call)

    with TestClient(hs.starlette_app) as client:
        response = client.post(
            "/api/tools/create_task",
            json={
                "title": "Ship contract tests",
                "project_id": "42",
                "priority": "critical",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 77

    assert captured["tool_name"] == "create_ticket"
    args = captured["arguments"]
    assert args["projectId"] == 42
    assert args["headline"] == "Ship contract tests"
    assert args["priority"] == "4"


def test_api_tools_endpoint_returns_400_for_invalid_request():
    """Missing required fields should fail validation before upstream call."""
    with TestClient(hs.starlette_app) as client:
        response = client.post("/api/tools/update_ticket", json={"status": "2"})

    assert response.status_code == 400
    assert "ticketId" in response.json()["error"]


@pytest.mark.asyncio
async def test_call_api_detects_install_redirect(monkeypatch):
    """Leantime install redirects should raise a setup-required bridge error."""

    class _RedirectResponse:
        status_code = 303
        headers = {"location": "http://leantime:80/install"}
        text = "<html>Redirecting to /install</html>"

        def raise_for_status(self):
            return None

    class _DummyAsyncClient:
        async def post(self, *args, **kwargs):  # noqa: ANN002, ANN003 - local test stub
            return _RedirectResponse()

    client = hs.LeantimeClient("http://leantime:80", "")
    client.client = _DummyAsyncClient()

    with pytest.raises(hs.LeantimeBridgeError, match="requires initial setup"):
        await client.call_api("leantime.rpc.Projects.getAllProjects", {})


def test_health_deep_reports_setup_required(monkeypatch):
    """Deep health should emit setup-required status when Leantime is uninitialized."""

    async def _raise_setup(client, tool_name: str, arguments: dict):  # noqa: ANN001
        raise hs.LeantimeBridgeError(
            "Leantime instance requires initial setup at /install before API calls can succeed"
        )

    monkeypatch.setattr(hs, "_call_tool_with_method_fallback", _raise_setup)

    with TestClient(hs.starlette_app) as client:
        response = client.get("/health?deep=1")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "needs_setup"
    assert payload["leantime"] == "setup_required"
    assert "/install" in payload["error"]
