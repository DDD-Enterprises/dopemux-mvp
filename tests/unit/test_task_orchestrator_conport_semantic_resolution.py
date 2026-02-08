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


def _load_module_with_temporary_stubs():
    """
    Load target module with isolated optional-dependency stubs.

    Important: restore `sys.modules` afterward so this test file does not poison
    imports for unrelated tests (for example `dopemux.mcp.*` package imports).
    """
    sentinel = object()
    saved = {}

    def _set_stub(name: str, module: types.ModuleType):
        saved[name] = sys.modules.get(name, sentinel)
        sys.modules[name] = module

    # Stub optional dopemux imports used by this module so tests can focus on
    # semantic-tool resolution logic in isolation.
    if "dopemux" not in sys.modules:
        dopemux_mod = types.ModuleType("dopemux")
        dopemux_mod.__path__ = []  # Mark as package.
        _set_stub("dopemux", dopemux_mod)

    if "dopemux.mcp" not in sys.modules:
        mcp_mod = types.ModuleType("dopemux.mcp")
        mcp_mod.__path__ = []  # Mark as package.
        _set_stub("dopemux.mcp", mcp_mod)

    if "dopemux.file_ops" not in sys.modules:
        file_ops_mod = types.ModuleType("dopemux.file_ops")
        file_ops_mod.__path__ = []  # Mark as package.
        _set_stub("dopemux.file_ops", file_ops_mod)

    parallel_executor_mod = types.ModuleType("dopemux.mcp.parallel_executor")
    parallel_executor_mod.MCPParallelExecutor = object
    _set_stub("dopemux.mcp.parallel_executor", parallel_executor_mod)

    batch_handler_mod = types.ModuleType("dopemux.file_ops.batch_handler")
    batch_handler_mod.BatchFileOps = object
    _set_stub("dopemux.file_ops.batch_handler", batch_handler_mod)

    try:
        SPEC.loader.exec_module(TASK_ORCH_MODULE)
    finally:
        for name, previous in saved.items():
            if previous is sentinel:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


_load_module_with_temporary_stubs()


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
