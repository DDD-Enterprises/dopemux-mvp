"""Contract tests for PM route integration with leantime-bridge."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

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
