"""PM dope-memory adapter sends instance_id on write calls (W2-F03)."""

import asyncio

import pytest

from dopemux.pm.adapters.dope_memory import DopeMemoryAdapter


class _Resp:
    def raise_for_status(self):
        pass

    def json(self):
        return {}


def _capture(monkeypatch):
    sent = {}

    async def fake(self, method, path, **kw):
        sent["path"] = path
        sent["json"] = kw["json"]
        return _Resp()

    monkeypatch.setattr(DopeMemoryAdapter, "_request", fake)
    return sent


def _append():
    return DopeMemoryAdapter("http://x").append_chronicle("ws", "note", "s", "manual")


def _correct():
    return DopeMemoryAdapter("http://x").correct_chronicle("ws", "e1", "summary", "s2")


@pytest.mark.parametrize("call", [_append, _correct])
def test_write_sends_env_instance_id(monkeypatch, call):
    sent = _capture(monkeypatch)
    monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", "ab12")
    asyncio.run(call())
    assert sent["json"]["instance_id"] == "ab12"


@pytest.mark.parametrize("call", [_append, _correct])
@pytest.mark.parametrize("raw", [None, "", "  ", "default"])
def test_write_omits_unresolvable_instance_id(monkeypatch, call, raw):
    sent = _capture(monkeypatch)
    if raw is None:
        monkeypatch.delenv("DOPE_MEMORY_INSTANCE_ID", raising=False)
    else:
        monkeypatch.setenv("DOPE_MEMORY_INSTANCE_ID", raw)
    asyncio.run(call())
    assert "instance_id" not in sent["json"]
