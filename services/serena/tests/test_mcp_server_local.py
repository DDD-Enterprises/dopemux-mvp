import json
from pathlib import Path
import sys
from unittest.mock import AsyncMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.mcp_server import SerenaV2MCPServer


def test_focus_mode_round_trip_mapping():
    server = SerenaV2MCPServer()

    for mode in ("focused", "transitioning", "scattered"):
        settings = server._focus_mode_settings(mode)
        inferred = server._infer_focus_mode_from_profile_row(
            {
                "optimal_result_limit": settings["result_limit"],
                "progressive_disclosure_preference": settings["progressive_disclosure"],
                "focus_mode_trigger_threshold": settings["focus_threshold"],
            }
        )
        assert inferred == mode


@pytest.mark.asyncio
async def test_update_focus_mode_reports_runtime_only_when_database_unavailable():
    server = SerenaV2MCPServer()
    server.workspace = Path("/tmp/serena-workspace")
    server._ensure_component = AsyncMock(return_value=False)

    payload = json.loads(await server.update_focus_mode_tool("scattered"))

    assert payload["mode"] == "scattered"
    assert payload["source"] == "runtime_only"
    assert payload["persistence"]["persisted"] is False
    assert payload["persistence"]["degraded"] is True
    assert payload["adhd"]["max_results"] == 3


@pytest.mark.asyncio
async def test_get_navigation_patterns_reports_history_unavailable_without_database():
    server = SerenaV2MCPServer()
    server.workspace = Path("/tmp/serena-workspace")
    server._ensure_component = AsyncMock(return_value=False)

    payload = json.loads(await server.get_navigation_patterns_tool(days_back=14))

    assert payload["status"] == "history_unavailable"
    assert payload["days_back"] == 14
    assert payload["patterns"] == []
    assert payload["provenance"]["degraded"] is True

@pytest.mark.asyncio
async def test_detect_untracked_work_enhanced_registration():
    server = SerenaV2MCPServer()

    list_tools_func = None
    call_tool_func = None

    def list_tools_mock():
        def decorator(f):
            nonlocal list_tools_func
            list_tools_func = f
            return f
        return decorator

    def call_tool_mock():
        def decorator(f):
            nonlocal call_tool_func
            call_tool_func = f
            return f
        return decorator

    server.server.list_tools = list_tools_mock
    server.server.call_tool = call_tool_mock

    server.register_tools()

    tools = await list_tools_func()
    tool_names = [t.name for t in tools]

    assert tool_names.count("detect_untracked_work_enhanced") == 1
    assert "detect_untracked_work" in tool_names
    assert "track_untracked_work" in tool_names
    assert "snooze_untracked_work" in tool_names
    assert "ignore_untracked_work" in tool_names

    server.detect_untracked_work_enhanced_tool = AsyncMock(return_value="mock_result")
    await call_tool_func("detect_untracked_work_enhanced", {"session_number": 2})
    server.detect_untracked_work_enhanced_tool.assert_called_once_with(session_number=2)

    result = await call_tool_func("not_a_real_tool", {})
    assert len(result) == 1
    assert "Unknown tool: not_a_real_tool" in result[0].text
