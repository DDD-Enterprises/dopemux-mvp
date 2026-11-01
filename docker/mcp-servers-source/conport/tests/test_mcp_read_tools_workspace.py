"""W1-F02: stdio/FastMCP get_decisions/get_progress must send a workspace_id."""
import asyncio
import sys
import types
from pathlib import Path

import pytest

CONPORT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONPORT_DIR))


class _FastMCPStub:
    def __init__(self, *a, **k):
        pass

    def tool(self, *a, **k):
        return lambda f: f

    def run(self, *a, **k):
        pass


for _n in ("mcp", "mcp.server", "mcp.server.fastmcp"):
    sys.modules.setdefault(_n, types.ModuleType(_n))
sys.modules["mcp.server.fastmcp"].__dict__.setdefault("FastMCP", _FastMCPStub)

pytest.importorskip("aiohttp")

import server  # noqa: E402
import conport_mcp_stdio  # noqa: E402

MODULES = [server, conport_mcp_stdio]


def _capture(mod, monkeypatch):
    urls = []

    async def fake_get_json(session, url):
        urls.append(url)
        return {"ok": True}

    monkeypatch.setattr(mod, "_get_json", fake_get_json)
    return urls


@pytest.mark.parametrize("mod", MODULES)
@pytest.mark.parametrize("bad", [None, "", "   "])
def test_get_decisions_rejects_missing_workspace(mod, bad, monkeypatch):
    urls = _capture(mod, monkeypatch)
    with pytest.raises(ValueError, match="workspace_id"):
        asyncio.run(mod.get_decisions(bad, 5))
    assert urls == []


@pytest.mark.parametrize("mod", MODULES)
@pytest.mark.parametrize("bad", [None, "", "   "])
def test_get_progress_rejects_missing_workspace(mod, bad, monkeypatch):
    urls = _capture(mod, monkeypatch)
    with pytest.raises(ValueError, match="workspace_id"):
        asyncio.run(mod.get_progress(bad, None, 5))
    assert urls == []


@pytest.mark.parametrize("mod", MODULES)
def test_reads_send_encoded_workspace(mod, monkeypatch):
    urls = _capture(mod, monkeypatch)
    ws = "/Users/hue/my repo&x=1"
    asyncio.run(mod.get_decisions(ws, 5))
    asyncio.run(mod.get_progress(ws, "DONE", 5))
    assert len(urls) == 2
    for u in urls:
        assert "workspace_id=%2FUsers%2Fhue%2Fmy+repo%26x%3D1" in u or "workspace_id=%2FUsers%2Fhue%2Fmy%20repo%26x%3D1" in u
