import json
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest


project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "docker/mcp-servers-source/conport"))

# Static poisoning at import time because conport_mcp_stdio imports from mcp.server.fastmcp
if "mcp" not in sys.modules:
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

@pytest.mark.asyncio
async def test_fastmcp_log_progress_defaults_to_in_progress(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict):
        captured["url"] = url
        captured["payload"] = payload
        return {"status": "logged", "progress": {"id": "p1"}}
    monkeypatch.setattr(conport_server, "_post_json", fake_post)
    result = await conport_server.log_progress("ws-1", "Ship docs")
    assert captured["url"].endswith("/api/progress")
    assert captured["payload"]["status"] == "IN_PROGRESS"
    assert json.loads(result)["status"] == "logged"

@pytest.mark.asyncio
async def test_stdio_log_progress_defaults_to_in_progress(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict):
        captured["payload"] = payload
        return {"status": "logged", "progress": {"id": "p2"}}
    monkeypatch.setattr(conport_mcp_stdio, "_post_json", fake_post)
    result = await conport_mcp_stdio.log_progress("ws-2", "Review drift")
    assert captured["payload"]["status"] == "IN_PROGRESS"
    assert json.loads(result)["status"] == "logged"

@pytest.mark.asyncio
async def test_fastmcp_log_decision_includes_summary_and_topic(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict):
        captured["payload"] = payload
        return {"status": "logged", "decision": {"id": "d1"}}
    monkeypatch.setattr(conport_server, "_post_json", fake_post)
    await conport_server.log_decision("ws-1", "architecture", "Prefer REST", "Lower drift")
    assert captured["payload"]["topic"] == "architecture"
    assert captured["payload"]["summary"] == "[architecture] Prefer REST"

@pytest.mark.asyncio
async def test_stdio_log_decision_includes_summary_and_topic(monkeypatch):
    captured = {}
    async def fake_post(url: str, payload: dict):
        captured["payload"] = payload
        return {"status": "logged", "decision": {"id": "d2"}}
    monkeypatch.setattr(conport_mcp_stdio, "_post_json", fake_post)
    await conport_mcp_stdio.log_decision("ws-2", "pm-plane", "Use REST", "Keep one contract")
    assert captured["payload"]["topic"] == "pm-plane"
    assert captured["payload"]["summary"] == "[pm-plane] Use REST"
