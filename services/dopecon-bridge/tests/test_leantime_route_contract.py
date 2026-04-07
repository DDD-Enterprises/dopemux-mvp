"""Contract tests for PM route integration with leantime-bridge."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

import main as bridge_main
import dopecon_bridge.routes as bridge_routes
from dopecon_bridge.clients import MCPClientManager
from dopecon_bridge.leantime_contract import (
    build_leantime_tool_request,
    normalize_leantime_route_response,
)


class _FakeResponse:
    def __init__(self, payload: dict | None = None, *, status: int = 200, text_body: str = ""):
        self._payload = payload
        self.status = status
        self._text_body = text_body

    def raise_for_status(self) -> None:
        return None

    async def json(self):
        return self._payload or {}

    async def text(self):
        if self._payload is not None:
            import json as _json

            return _json.dumps(self._payload)
        return self._text_body

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, payload: dict | None = None, *, status: int = 200, text_body: str = ""):
        self.payload = payload
        self.status = status
        self.text_body = text_body
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, json: dict):
        self.calls.append((url, json))
        return _FakeResponse(self.payload, status=self.status, text_body=self.text_body)


@pytest.fixture
def runtime_client(monkeypatch):
    monkeypatch.setattr(bridge_main, "init_default_users", lambda: None)
    monkeypatch.setattr(bridge_main.db_manager, "initialize", AsyncMock())
    monkeypatch.setattr(bridge_main.cache_manager, "initialize", AsyncMock())
    monkeypatch.setattr(bridge_main.db_manager, "close", AsyncMock())
    monkeypatch.setattr(bridge_main.cache_manager, "close", AsyncMock())
    monkeypatch.setattr(bridge_routes.mcp_client, "health_check_all", AsyncMock(return_value={}))
    monkeypatch.setattr(bridge_routes.conport_client, "health_check", AsyncMock(return_value=True))

    with TestClient(bridge_main.app) as client:
        yield client


@pytest.mark.asyncio
async def test_mcp_client_uses_api_tools_endpoint(monkeypatch):
    """MCP client contract: route tool calls through `/api/tools/{tool}`."""
    manager = MCPClientManager()
    manager.session = _FakeSession({"ok": True, "id": 1})

    monkeypatch.setattr(manager, "_get_service_url", lambda _service: "http://leantime-bridge:3015")

    result = await manager.call_tool(
        "leantime-bridge",
        "list_tickets",
        {"projectId": 9},
    )

    assert result["ok"] is True
    assert manager.session.calls[0][0] == "http://leantime-bridge:3015/api/tools/list_tickets"
    assert manager.session.calls[0][1] == {"projectId": 9}


def test_route_contract_create_task_translation():
    """`leantime.create_task` should map to `create_ticket` payload."""
    tool_name, payload = build_leantime_tool_request(
        "leantime.create_task",
        {
            "title": "Ship docs",
            "project_id": "42",
            "priority": "high",
        },
    )

    assert tool_name == "create_ticket"
    assert payload == {
        "projectId": 42,
        "headline": "Ship docs",
        "description": "",
        "priority": "3",
        "type": "task",
    }


def test_route_contract_get_tasks_translation_and_response_shape():
    """`get_tasks` should map to list_tickets and normalize to `tasks` list."""
    tool_name, payload = build_leantime_tool_request(
        "get_tasks",
        {"project_id": "7", "status": "TODO"},
    )
    assert tool_name == "list_tickets"
    assert payload == {"projectId": 7, "status": "TODO"}

    normalized = normalize_leantime_route_response(
        "get_tasks",
        [{"id": 1, "headline": "A"}],
    )
    assert isinstance(normalized["tasks"], list)
    assert normalized["tasks"][0]["id"] == 1


def test_route_contract_allocate_resource_translation_and_response_shape():
    """`allocate_resource` should map to ticket assignment update semantics."""
    tool_name, payload = build_leantime_tool_request(
        "leantime.allocate_resource",
        {
            "resource_type": "user",
            "resource_id": "5",
            "allocation": {
                "task_id": "11",
            },
        },
    )

    assert tool_name == "update_ticket"
    assert payload == {"ticketId": 11, "assignedTo": 5}

    normalized = normalize_leantime_route_response(
        "leantime.allocate_resource",
        {"ticketId": 11, "assignedTo": 5},
    )
    assert normalized["allocated"] is True


@pytest.mark.asyncio
async def test_mcp_client_includes_leantime_setup_hint_on_upstream_error(monkeypatch):
    manager = MCPClientManager()
    manager.session = _FakeSession(status=503, text_body="LEANTIME_API_TOKEN not configured")
    monkeypatch.setattr(manager, "_get_service_url", lambda _service: "http://leantime-bridge:3015")

    with pytest.raises(HTTPException) as exc:
        await manager.call_tool("leantime-bridge", "list_tickets", {"projectId": 9})

    assert exc.value.status_code == 502
    assert "Leantime readiness hint" in exc.value.detail
    assert "LEANTIME_API_TOKEN" in exc.value.detail


@pytest.mark.asyncio
async def test_mcp_client_preserves_non_leantime_status_context(monkeypatch):
    manager = MCPClientManager()
    manager.session = _FakeSession(status=500, text_body="upstream failure")
    monkeypatch.setattr(manager, "_get_service_url", lambda _service: "http://task-orchestrator:3014")

    with pytest.raises(HTTPException) as exc:
        await manager.call_tool("task-orchestrator", "analyze_dependencies", {"tasks": []})

    assert exc.value.status_code == 502
    assert "task-orchestrator.analyze_dependencies" in exc.value.detail
    assert "upstream status 500" in exc.value.detail


def test_event_publish_requires_auth(runtime_client):
    response = runtime_client.post(
        "/events",
        json={"event_type": "bridge.test", "data": {"count": 1}},
    )

    assert response.status_code in {401, 403}


def test_legacy_task_routes_fail_closed(runtime_client):
    next_response = runtime_client.get("/tasks/next/project-1")
    parse_response = runtime_client.post(
        "/tasks/parse-prd",
        json={"content": "PRD", "project_id": "project-1"},
    )

    bridge_main.app.dependency_overrides[bridge_routes.get_current_user] = lambda: {"username": "admin"}
    status_response = runtime_client.patch(
        "/tasks/task-1/status",
        json={"status": "completed"},
    )
    bridge_main.app.dependency_overrides.clear()

    assert next_response.status_code == 409
    assert parse_response.status_code == 409
    assert status_response.status_code == 409


def test_route_pm_blocks_workflow_significant_mutations(runtime_client):
    bridge_main.app.dependency_overrides[bridge_routes.get_current_user] = lambda: {"username": "admin"}
    response = runtime_client.post(
        "/route/pm",
        json={
            "operation": "update_task_status",
            "data": {"task_id": "123", "status": "DONE"},
            "requester": "pytest",
        },
    )
    bridge_main.app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "Task Orchestrator adjudication" in response.text


def test_route_pm_proxies_safe_leantime_operation(runtime_client, monkeypatch):
    mock_call = AsyncMock(return_value=[{"id": 1, "headline": "Ship docs"}])
    monkeypatch.setattr(bridge_routes.mcp_client, "call_tool", mock_call)

    bridge_main.app.dependency_overrides[bridge_routes.get_current_user] = lambda: {"username": "admin"}
    response = runtime_client.post(
        "/route/pm",
        json={
            "operation": "get_tasks",
            "data": {"project_id": "7"},
            "requester": "pytest",
        },
    )
    bridge_main.app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["tasks"][0]["id"] == 1
    mock_call.assert_awaited_once_with("leantime-bridge", "list_tickets", {"projectId": 7})


def test_ddg_and_custom_data_routes_proxy_to_conport(runtime_client, monkeypatch):
    monkeypatch.setattr(
        bridge_routes.conport_client,
        "list_decisions",
        AsyncMock(return_value={"count": 1, "decisions": [{"id": "dec_1"}]}),
    )
    monkeypatch.setattr(
        bridge_routes.conport_client,
        "get_custom_data",
        AsyncMock(return_value={"count": 1, "items": [{"key": "foo", "value": {"bar": 1}}]}),
    )

    bridge_main.app.dependency_overrides[bridge_routes.get_current_user] = lambda: {"username": "admin"}
    ddg_response = runtime_client.get("/ddg/decisions", params={"workspace_id": "/workspace", "limit": 5})
    custom_response = runtime_client.get(
        "/kg/custom_data",
        params={"workspace_id": "/workspace", "category": "test", "limit": 5},
    )
    bridge_main.app.dependency_overrides.clear()

    assert ddg_response.status_code == 200
    assert ddg_response.json()["items"] == [{"id": "dec_1"}]
    assert custom_response.status_code == 200
    assert custom_response.json()["data"] == [{"key": "foo", "value": {"bar": 1}}]


def test_custom_data_route_normalizes_upstream_empty_state(runtime_client, monkeypatch):
    monkeypatch.setattr(
        bridge_routes.conport_client,
        "get_custom_data",
        AsyncMock(return_value={"count": 0, "items": []}),
    )

    bridge_main.app.dependency_overrides[bridge_routes.get_current_user] = lambda: {"username": "admin"}
    response = runtime_client.get(
        "/kg/custom_data",
        params={"workspace_id": "/workspace", "category": "workflow_ideas", "limit": 5},
    )
    bridge_main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "count": 0,
        "data": [],
        "source": "conport",
    }
