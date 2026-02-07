import importlib.util
import sys
import types
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "task-orchestrator"
    / "conport_mcp_client.py"
)

SPEC = importlib.util.spec_from_file_location("task_orch_conport_client_for_tests", MODULE_PATH)
TASK_ORCH_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader

# Stub optional dopemux imports used by this module so tests can focus on
# semantic-tool resolution logic in isolation.
if "dopemux" not in sys.modules:
    sys.modules["dopemux"] = types.ModuleType("dopemux")
if "dopemux.mcp" not in sys.modules:
    sys.modules["dopemux.mcp"] = types.ModuleType("dopemux.mcp")
if "dopemux.file_ops" not in sys.modules:
    sys.modules["dopemux.file_ops"] = types.ModuleType("dopemux.file_ops")

parallel_executor_mod = types.ModuleType("dopemux.mcp.parallel_executor")
parallel_executor_mod.MCPParallelExecutor = object
sys.modules["dopemux.mcp.parallel_executor"] = parallel_executor_mod

batch_handler_mod = types.ModuleType("dopemux.file_ops.batch_handler")
batch_handler_mod.BatchFileOps = object
sys.modules["dopemux.file_ops.batch_handler"] = batch_handler_mod

SPEC.loader.exec_module(TASK_ORCH_MODULE)


@pytest.mark.asyncio
async def test_semantic_search_prefers_primary_tool():
    calls = []

    class _Tools:
        async def mcp__conport__semantic_search(self, **kwargs):
            calls.append(("primary", kwargs))
            return {"results": [{"id": "primary"}]}

        async def mcp__conport__semantic_search_conport(self, **kwargs):
            calls.append(("legacy", kwargs))
            return {"results": [{"id": "legacy"}]}

    client = TASK_ORCH_MODULE.ConPortMCPClient(_Tools())
    result = await client.semantic_search(
        workspace_id="/tmp/ws",
        query_text="auth",
        top_k=7,
    )

    assert len(calls) == 1
    assert calls[0][0] == "primary"
    assert calls[0][1]["top_k"] == "7"
    assert result.get("_tool_used") == "mcp__conport__semantic_search"


@pytest.mark.asyncio
async def test_semantic_search_uses_legacy_fallback_tool():
    calls = []

    class _Tools:
        async def mcp__conport__semantic_search_conport(self, **kwargs):
            calls.append(kwargs)
            return {"results": [{"id": "legacy"}]}

    client = TASK_ORCH_MODULE.ConPortMCPClient(_Tools())
    result = await client.semantic_search(
        workspace_id="/tmp/ws",
        query_text="auth",
        top_k=99,
    )

    assert len(calls) == 1
    # top_k is clamped to max 25 then converted to string
    assert calls[0]["top_k"] == "25"
    assert result.get("_tool_used") == "mcp__conport__semantic_search_conport"


@pytest.mark.asyncio
async def test_semantic_search_raises_when_no_tool_available():
    class _Tools:
        pass

    client = TASK_ORCH_MODULE.ConPortMCPClient(_Tools())
    with pytest.raises(AttributeError):
        await client.semantic_search(
            workspace_id="/tmp/ws",
            query_text="auth",
            top_k=5,
        )


@pytest.mark.asyncio
async def test_legacy_alias_delegates_to_primary_method():
    calls = []

    class _Tools:
        async def mcp__conport__semantic_search(self, **kwargs):
            calls.append(kwargs)
            return {"results": [{"id": "primary"}]}

    client = TASK_ORCH_MODULE.ConPortMCPClient(_Tools())
    result = await client.semantic_search_conport(
        workspace_id="/tmp/ws",
        query_text="auth",
        top_k=3,
    )

    assert len(calls) == 1
    assert calls[0]["top_k"] == "3"
    assert result.get("_tool_used") == "mcp__conport__semantic_search"
