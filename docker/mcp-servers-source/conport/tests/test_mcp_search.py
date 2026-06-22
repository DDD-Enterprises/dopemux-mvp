import asyncio
import inspect
import json
import sys
import types
from pathlib import Path


CONPORT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONPORT_DIR))


class _FastMCPStub:
    def __init__(self, *args, **kwargs):
        self.tools = []

    def tool(self):
        def decorator(func):
            self.tools.append(func.__name__)
            return func

        return decorator


fastmcp_module = types.ModuleType("mcp.server.fastmcp")
fastmcp_module.FastMCP = _FastMCPStub
mcp_module = types.ModuleType("mcp")
mcp_server_module = types.ModuleType("mcp.server")
mcp_server_models_module = types.ModuleType("mcp.server.models")
mcp_server_models_module.InitializationOptions = object
mcp_server_stdio_module = types.ModuleType("mcp.server.stdio")
mcp_server_stdio_module.stdio_server = object

sys.modules.setdefault("mcp", mcp_module)
sys.modules.setdefault("mcp.server", mcp_server_module)
sys.modules.setdefault("mcp.server.fastmcp", fastmcp_module)
sys.modules.setdefault("mcp.server.models", mcp_server_models_module)
sys.modules.setdefault("mcp.server.stdio", mcp_server_stdio_module)

import conport_mcp_stdio
import server as mcp_server
from enhanced_server import EnhancedConPortServer


def _response_json(response):
    return json.loads(response.text)


def test_jsonrpc_search_content_tool_is_advertised():
    app = EnhancedConPortServer()

    tools = {tool["name"]: tool for tool in app._get_tool_schemas()}

    assert "conport_search_content" in tools
    assert tools["conport_search_content"]["inputSchema"]["required"] == [
        "workspace_id",
        "query",
    ]


def test_jsonrpc_search_content_dispatch_returns_seeded_result(monkeypatch):
    app = EnhancedConPortServer()
    seeded = {
        "workspace_id": "ws-105",
        "query": "needle",
        "results": {
            "decisions": [
                {
                    "id": "decision-1",
                    "workspace_id": "ws-105",
                    "summary": "needle decision",
                    "rationale": "seeded result",
                    "rank": 0.5,
                }
            ],
            "progress": [],
        },
        "total_count": 1,
    }

    async def fake_search(args):
        assert args == {"workspace_id": "ws-105", "query": "needle"}
        return seeded

    monkeypatch.setattr(app, "_search_content_tool", fake_search, raising=False)

    response = _response_json(
        asyncio.run(
            app._dispatch_tool(
                1,
                "conport_search_content",
                {"workspace_id": "ws-105", "query": "needle"},
            )
        )
    )

    assert response["result"]["total_count"] == 1
    assert response["result"]["results"]["decisions"][0]["summary"] == "needle decision"


def test_fastmcp_modules_expose_search_content_tool_function():
    for module in (mcp_server, conport_mcp_stdio):
        tool = getattr(module, "search_content")
        assert inspect.iscoroutinefunction(tool)
