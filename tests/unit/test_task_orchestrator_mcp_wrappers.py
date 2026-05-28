import sys
from pathlib import Path

import pytest


SERVICE_ROOT = Path("services/task-orchestrator").resolve()
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def test_task_orchestrator_mcp_registers_read_only_wrapper_tools():
    from task_orchestrator.mcp import MCP_TOOLS

    tool_names = {tool["name"] for tool in MCP_TOOLS}

    assert "orchestrator.status.queue" in tool_names
    assert "orchestrator.status.blockers" in tool_names
    assert "orchestrator.status.state" in tool_names
    assert "orchestrator.daily.summary" in tool_names
    assert "orchestrator.packet.validate" in tool_names
    assert "orchestrator.proof.validate" in tool_names


@pytest.mark.asyncio
async def test_task_orchestrator_mcp_dispatches_read_only_wrappers(monkeypatch):
    import task_orchestrator.mcp as service_mcp

    async def fake_handle(tool_name: str, arguments: dict):
        return {
            "tool": tool_name,
            "arguments": arguments,
            "read_only": True,
        }

    monkeypatch.setattr(service_mcp, "handle_orchestrator_tool_call", fake_handle)

    payload = await service_mcp.handle_tool_call(
        "orchestrator.status.queue",
        {"project_id": "dopemux-mvp"},
    )

    assert payload == {
        "tool": "orchestrator.status.queue",
        "arguments": {"project_id": "dopemux-mvp"},
        "read_only": True,
    }
