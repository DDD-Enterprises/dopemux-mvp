from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path

import httpx
import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
MODULE_PATH = SERVICE_ROOT / "app" / "services" / "workflow_store.py"


def _load_workflow_store_module():
    service_root_str = str(SERVICE_ROOT)
    if service_root_str in sys.path:
        sys.path.remove(service_root_str)
    sys.path.insert(0, service_root_str)

    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    module_name = f"task_orchestrator_workflow_store_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_workflow_store_list_ideas_returns_empty_for_empty_bridge_payload():
    module = _load_workflow_store_module()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/kg/custom_data"
        assert request.url.params["category"] == "workflow_ideas"
        return httpx.Response(200, json={"success": True, "count": 0, "data": []})

    store = module.WorkflowStore(workspace_id="/workspace")
    await store._client.aclose()
    store._client = module.AsyncDopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    try:
        ideas = await store.list_ideas(limit=5)
    finally:
        await store.close()

    assert ideas == []


@pytest.mark.asyncio
async def test_workflow_store_list_ideas_raises_on_bridge_failure():
    module = _load_workflow_store_module()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="bridge unavailable")

    store = module.WorkflowStore(workspace_id="/workspace")
    await store._client.aclose()
    store._client = module.AsyncDopeconBridgeClient(
        base_url="http://bridge",
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(module.WorkflowStoreError, match="503"):
            await store.list_ideas(limit=5)
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_workflow_store_replays_same_identity_as_authenticated_upsert():
    module = _load_workflow_store_module()
    persisted = {}
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/kg/custom_data"
        assert request.headers["authorization"] == "Bearer synthetic-bridge-token"
        payload = json.loads(request.content)
        identity = (payload["workspace_id"], payload["category"], payload["key"])
        persisted[identity] = payload["value"]
        requests.append(identity)
        return httpx.Response(200, json={"success": True, "status": "saved"})

    store = module.WorkflowStore(workspace_id="/synthetic/workspace")
    await store._client.aclose()
    store._client = module.AsyncDopeconBridgeClient(
        base_url="http://bridge",
        token="synthetic-bridge-token",
        transport=httpx.MockTransport(handler),
    )

    try:
        assert await store.save_idea({"id": "idea_replay", "title": "first"}) is True
        assert await store.save_idea({"id": "idea_replay", "title": "second"}) is True
    finally:
        await store.close()

    identity = ("/synthetic/workspace", "workflow_ideas", "idea_replay")
    assert requests == [identity, identity]
    assert persisted == {identity: {"id": "idea_replay", "title": "second"}}
