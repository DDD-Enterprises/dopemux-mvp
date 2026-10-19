"""W1-F02: ConPortClient.get_progress must never issue a workspace-less GET."""
import pytest

from ..conport_client import ConPortClient


class _Resp:
    status = 200

    async def json(self):
        return {"progress": []}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Session:
    closed = False

    def __init__(self):
        self.calls = []

    def get(self, url, params=None):
        self.calls.append((url, params))
        return _Resp()


@pytest.mark.asyncio
@pytest.mark.parametrize("ws", [None, "", "  "])
async def test_get_progress_without_workspace_fails_without_request(ws):
    c = ConPortClient()
    c.session = _Session()
    result = await c.get_progress(workspace_id=ws)
    assert "workspace_id" in result.get("error", "")
    assert c.session.calls == []


@pytest.mark.asyncio
async def test_get_progress_sends_workspace():
    c = ConPortClient()
    c.session = _Session()
    await c.get_progress(workspace_id="/ws/a")
    assert c.session.calls[0][1]["workspace_id"] == "/ws/a"
