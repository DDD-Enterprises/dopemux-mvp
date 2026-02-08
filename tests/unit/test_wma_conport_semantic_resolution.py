import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "working-memory-assistant"
    / "conport_client.py"
)

SPEC = importlib.util.spec_from_file_location("wma_conport_client_for_tests", MODULE_PATH)
WMA_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WMA_MODULE)


@pytest.mark.asyncio
async def test_wma_semantic_search_uses_configured_tool(monkeypatch):
    captured = {}

    async def _fake_tool(**kwargs):
        captured.update(kwargs)
        return {"results": [{"id": "d1"}]}

    monkeypatch.setattr(WMA_MODULE, "_semantic_search_tool", _fake_tool)
    monkeypatch.setattr(WMA_MODULE, "_semantic_search_tool_name", "test_primary_tool")

    client = WMA_MODULE.ConPortClient(workspace_id="/tmp/ws")
    results = await client.semantic_search(query="auth flow", top_k=4)

    assert results == [{"id": "d1"}]
    assert captured["workspace_id"] == "/tmp/ws"
    assert captured["query_text"] == "auth flow"
    assert captured["top_k"] == 4


@pytest.mark.asyncio
async def test_wma_semantic_search_accepts_list_result(monkeypatch):
    async def _fake_tool(**_kwargs):
        return [{"id": "list_item"}]

    monkeypatch.setattr(WMA_MODULE, "_semantic_search_tool", _fake_tool)

    client = WMA_MODULE.ConPortClient(workspace_id="/tmp/ws")
    results = await client.semantic_search(query="auth", top_k=2)

    assert results == [{"id": "list_item"}]


@pytest.mark.asyncio
async def test_wma_semantic_search_returns_empty_on_tool_error(monkeypatch):
    async def _failing_tool(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(WMA_MODULE, "_semantic_search_tool", _failing_tool)

    client = WMA_MODULE.ConPortClient(workspace_id="/tmp/ws")
    results = await client.semantic_search(query="auth", top_k=2)

    assert results == []
