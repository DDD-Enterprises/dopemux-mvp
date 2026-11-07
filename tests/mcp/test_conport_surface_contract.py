import json
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest


project_root = Path(__file__).resolve().parents[2]
_CONPORT_DIR = str(project_root / "docker/mcp-servers-source/conport")
_CONPORT_MODULES = ("auth_identity", "instance_detector", "conport_mcp_stdio", "server")
_saved_conport_modules = {
    name: sys.modules.pop(name, None) for name in _CONPORT_MODULES
}
sys.path.insert(0, _CONPORT_DIR)

# Static poisoning at import time because conport_mcp_stdio imports from mcp.server.fastmcp
_MCP_STUBBED = "mcp" not in sys.modules
if _MCP_STUBBED:
    mcp_module = types.ModuleType("mcp")
    server_module = types.ModuleType("mcp.server")
    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    models_module = types.ModuleType("mcp.server.models")
    stdio_module = types.ModuleType("mcp.server.stdio")

    class _FakeFastMCP:
        def __init__(self, *args, **kwargs):
            self.tools = {}
        def tool(self, name=None, description=None):
            def decorator(func):
                return func
            return decorator
        def sse_app(self): return object()
        async def run_stdio_async(self): return None
        def run(self, transport="stdio"): return None

    class _InitializationOptions: pass
    async def _stdio_server(*args, **kwargs): return None

    fastmcp_module.FastMCP = _FakeFastMCP
    fastmcp_module.Context = object
    models_module.InitializationOptions = _InitializationOptions
    stdio_module.stdio_server = _stdio_server
    mcp_module.server = server_module
    server_module.fastmcp = fastmcp_module
    server_module.models = models_module
    server_module.stdio = stdio_module
    
    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.server"] = server_module
    sys.modules["mcp.server.fastmcp"] = fastmcp_module
    sys.modules["mcp.server.models"] = models_module
    sys.modules["mcp.server.stdio"] = stdio_module

import conport_mcp_stdio  # noqa: E402
import server as conport_server  # noqa: E402

# Leave nothing behind. A stub left in sys.modules makes other test modules'
# pytest.importorskip("mcp.server.fastmcp") succeed against it, and ConPort's
# auth_identity would shadow dope-memory's module of the same name.
sys.path.remove(_CONPORT_DIR)
for _name, _module in _saved_conport_modules.items():
    sys.modules.pop(_name, None)
    if _module is not None:
        sys.modules[_name] = _module
if _MCP_STUBBED:
    for _name in [m for m in sys.modules if m == "mcp" or m.startswith("mcp.")]:
        del sys.modules[_name]

@pytest.mark.asyncio
async def test_fastmcp_log_progress_defaults_to_in_progress(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict, headers: Optional[dict] = None):
        captured["url"] = url
        captured["payload"] = payload
        return {"status": "logged", "progress": {"id": "p1"}}
    monkeypatch.setattr(conport_server, "_post_json", fake_post)
    result = await conport_server.log_progress("Ship docs", workspace_id="ws-1")
    assert captured["url"].endswith("/api/progress")
    assert captured["payload"]["status"] == "IN_PROGRESS"
    assert json.loads(result)["status"] == "logged"

@pytest.mark.asyncio
async def test_stdio_log_progress_defaults_to_in_progress(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict, headers: Optional[dict] = None):
        captured["payload"] = payload
        return {"status": "logged", "progress": {"id": "p2"}}
    monkeypatch.setattr(conport_mcp_stdio, "_post_json", fake_post)
    result = await conport_mcp_stdio.log_progress("Review drift", workspace_id="ws-2")
    assert captured["payload"]["status"] == "IN_PROGRESS"
    assert json.loads(result)["status"] == "logged"

@pytest.mark.asyncio
async def test_fastmcp_log_decision_includes_summary_and_topic(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict, headers: Optional[dict] = None):
        captured["payload"] = payload
        return {"status": "logged", "decision": {"id": "d1"}}
    monkeypatch.setattr(conport_server, "_post_json", fake_post)
    await conport_server.log_decision(
        "architecture", "Prefer REST", "Lower drift", workspace_id="ws-1"
    )
    assert captured["payload"]["topic"] == "architecture"
    assert captured["payload"]["summary"] == "[architecture] Prefer REST"

@pytest.mark.asyncio
async def test_stdio_log_decision_includes_summary_and_topic(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict, headers: Optional[dict] = None):
        captured["payload"] = payload
        return {"status": "logged", "decision": {"id": "d2"}}
    monkeypatch.setattr(conport_mcp_stdio, "_post_json", fake_post)
    await conport_mcp_stdio.log_decision(
        "pm-plane", "Use REST", "Keep one contract", workspace_id="ws-2"
    )
    assert captured["payload"]["topic"] == "pm-plane"
    assert captured["payload"]["summary"] == "[pm-plane] Use REST"
