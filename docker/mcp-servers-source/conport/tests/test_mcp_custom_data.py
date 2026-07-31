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

    def tool(self, *, name=None, description=None):
        def decorator(func):
            self.tools.append(name or func.__name__)
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

import conport_mcp_stdio  # noqa: E402
import server as mcp_server  # noqa: E402
from enhanced_server import EnhancedConPortServer  # noqa: E402


def _response_json(response):
    return json.loads(response.text)


def test_jsonrpc_custom_data_tools_are_advertised():
    app = EnhancedConPortServer()

    tools = {tool["name"]: tool for tool in app._get_tool_schemas()}

    assert set(tools) >= {
        "conport_get_custom_data",
        "conport_save_custom_data",
        "conport_delete_custom_data",
    }
    assert tools["conport_get_custom_data"]["inputSchema"]["required"] == ["workspace_id"]
    assert tools["conport_save_custom_data"]["inputSchema"]["required"] == [
        "workspace_id",
        "category",
        "key",
        "value",
    ]
    assert tools["conport_delete_custom_data"]["inputSchema"]["required"] == [
        "workspace_id",
        "category",
        "key",
    ]


def test_jsonrpc_custom_data_dispatch_round_trip(monkeypatch):
    app = EnhancedConPortServer()
    store = {}

    async def fake_save(args):
        store[(args["workspace_id"], args["category"], args["key"])] = args["value"]
        return {
            "status": "saved",
            "workspace_id": args["workspace_id"],
            "category": args["category"],
            "key": args["key"],
        }

    async def fake_get(args):
        value = store[(args["workspace_id"], args["category"], args["key"])]
        return {
            "workspace_id": args["workspace_id"],
            "category": args["category"],
            "key": args["key"],
            "value": value,
        }

    async def fake_delete(args):
        store.pop((args["workspace_id"], args["category"], args["key"]))
        return {
            "status": "deleted",
            "workspace_id": args["workspace_id"],
            "category": args["category"],
            "key": args["key"],
        }

    monkeypatch.setattr(app, "_save_custom_data_tool", fake_save, raising=False)
    monkeypatch.setattr(app, "_get_custom_data_tool", fake_get, raising=False)
    monkeypatch.setattr(app, "_delete_custom_data_tool", fake_delete, raising=False)

    save_args = {
        "workspace_id": "ws-104",
        "category": "agent",
        "key": "mode",
        "value": {"enabled": True},
    }

    save = _response_json(
        asyncio.run(app._dispatch_tool(1, "conport_save_custom_data", save_args))
    )
    get = _response_json(
        asyncio.run(app._dispatch_tool(2, "conport_get_custom_data", save_args))
    )
    delete = _response_json(
        asyncio.run(app._dispatch_tool(3, "conport_delete_custom_data", save_args))
    )

    assert save["result"]["status"] == "saved"
    assert get["result"]["value"] == {"enabled": True}
    assert delete["result"]["status"] == "deleted"
    assert store == {}


def test_fastmcp_modules_expose_custom_data_tool_functions():
    for module in (mcp_server, conport_mcp_stdio):
        for tool_name in ("get_custom_data", "save_custom_data", "delete_custom_data"):
            tool = getattr(module, tool_name)
            assert inspect.iscoroutinefunction(tool)
