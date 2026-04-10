from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from services.shared.dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeClient,
    DopeconBridgeError,
)


def test_publish_event_sync_client() -> None:
    """Ensure the sync client sends the right payload and parses the response."""

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["payload"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={
                "status": "published",
                "message_id": "1701-1",
                "stream": "dopemux:events",
                "event_type": "tasks_imported",
                "timestamp": "2025-11-13T00:00:00Z",
            },
        )

    client = DopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    response = client.publish_event(event_type="tasks_imported", data={"count": 1})

    client.close()

    assert captured["url"].endswith("/events")
    assert captured["payload"]["event_type"] == "tasks_imported"
    assert captured["payload"]["data"] == {"count": 1}
    assert response.status == "published"
    assert response.message_id == "1701-1"


def test_route_pm_async_client() -> None:
    """The async client should hit /route/pm and parse CrossPlaneRouteResponse."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/route/pm"
        body = json.loads(request.content)
        assert body["operation"] == "get_tasks"
        assert body["requester"] == "test-service"
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {"tasks": []},
                "correlation_id": "abc-123",
            },
        )

    async def _run() -> None:
        client = AsyncDopeconBridgeClient(
            base_url="http://bridge",
            transport=httpx.MockTransport(handler),
        )

        response = await client.route_pm(
            operation="get_tasks",
            data={"limit": 5},
            requester="test-service",
        )

        await client.aclose()

        assert response.success is True
        assert response.data == {"tasks": []}
        assert response.correlation_id == "abc-123"

    asyncio.run(_run())


def test_error_response_raises_bridge_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = DopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(DopeconBridgeError):
        client.get_stream_info("dopemux:events")

    client.close()


def test_bridge_client_preserves_unrelated_404_as_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing stream")

    client = DopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(DopeconBridgeError, match="404"):
        client.get_stream_info("missing")

    client.close()


def test_save_and_get_custom_data() -> None:
    """Saving custom data should set headers and return success."""

    calls = {}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.setdefault(request.url.path, []).append(request)
        if request.method == "POST":
            assert request.headers["X-Source-Plane"] == "cognitive_plane"
            body = json.loads(request.content)
            assert body["workspace_id"] == "/workspace"
            return httpx.Response(200, json={"success": True})
        else:
            return httpx.Response(200, json={"data": [{"key": "foo", "value": {"count": 1}}]})

    client = DopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    assert client.save_custom_data(
        workspace_id="/workspace",
        category="test",
        key="foo",
        value={"count": 1},
    ) is True

    data = client.get_custom_data(
        workspace_id="/workspace",
        category="test",
        limit=5,
    )

    client.close()

    assert data == [{"key": "foo", "value": {"count": 1}}]
    assert "/kg/custom_data" in calls


def test_recent_and_search_decisions_use_active_ddg_routes() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, dict(request.url.params)))
        return httpx.Response(
            200,
            json={
                "count": 1,
                "items": [{"id": "dec_1", "summary": "Keep adapter-only bridge"}],
            },
        )

    client = DopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    recent = client.recent_decisions(workspace_id="/workspace", limit=5)
    search = client.search_decisions(query="adapter", workspace_id="/workspace", limit=3)

    client.close()

    assert recent.count == 1
    assert search.items[0]["id"] == "dec_1"
    assert calls[0][1] == "/ddg/decisions"
    assert calls[1][1] == "/ddg/search"


def test_unsupported_bridge_surfaces_raise_explicit_errors() -> None:
    client = DopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
    )

    with pytest.raises(DopeconBridgeError, match="deprecated or blocked"):
        client.route_cognitive(operation="noop", data={}, requester="tester")

    with pytest.raises(DopeconBridgeError, match="deprecated or blocked"):
        client.related_decisions(decision_id="dec_1")

    with pytest.raises(DopeconBridgeError, match="deprecated or blocked"):
        client.related_text(query="adapter")

    with pytest.raises(DopeconBridgeError, match="deprecated or blocked"):
        client.create_link(
            source_item_type="decision",
            source_item_id="a",
            target_item_type="progress",
            target_item_id="b",
            relationship_type="supports",
        )

    client.close()
