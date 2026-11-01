"""R1-D: event intake identity fail-closed (W2-F02). Fakes only; no Redis."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from eventbus_consumer import EventBusConsumer


def _consumer(tmp_path, monkeypatch, own_ws=None, own_inst=None):
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "chronicle.sqlite"))
    for key, val in (("DOPE_MEMORY_WORKSPACE_ID", own_ws), ("DOPE_MEMORY_INSTANCE_ID", own_inst)):
        if val is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, val)
    c = EventBusConsumer(redis_url="redis://unused:6379")
    c.redis_client = AsyncMock()
    return c


def _msg(workspace=b"ws-own", instance=b"A", **extra):
    m = {
        b"id": b"evt-1",
        b"ts": b"2026-02-02T10:00:00Z",
        b"type": b"decision.logged",
        b"source": b"dopequery",
        b"data": json.dumps(
            {"decision_id": "d-1", "title": "Use SQLite", "choice": "SQLite", "rationale": "simple"}
        ).encode(),
    }
    if workspace is not None:
        m[b"workspace_id"] = workspace
    if instance is not None:
        m[b"instance_id"] = instance
    m.update(extra)
    return m


def _promoted(c, ws, inst="A"):
    return c._get_store(ws).search_work_log(workspace_id=ws, instance_id=inst, query="SQLite", limit=10)


@pytest.mark.asyncio
@pytest.mark.parametrize("msg", [
    _msg(workspace=None),
    _msg(workspace=b"   "),
    _msg(instance=None),
    _msg(instance=b""),
])
async def test_missing_or_blank_identity_not_promoted(tmp_path, monkeypatch, msg):
    c = _consumer(tmp_path, monkeypatch)
    await c._process_message(b"m1", msg)  # returns normally => caller acks
    assert _promoted(c, "default") == []
    assert _promoted(c, "default", "A") == []
    assert c.metrics["rejected_missing_identity"] == 1
    c.redis_client.xadd.assert_not_called()


@pytest.mark.asyncio
async def test_foreign_workspace_not_promoted(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="ws-own")
    await c._process_message(b"m2", _msg(workspace=b"ws-other"))
    assert _promoted(c, "ws-other") == []
    assert c.metrics["rejected_foreign_workspace"] == 1


@pytest.mark.asyncio
async def test_foreign_instance_not_promoted_when_own_instance_set(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="ws-own", own_inst="A")
    await c._process_message(b"m3", _msg(instance=b"B"))
    assert _promoted(c, "ws-own", "B") == []
    assert c.metrics["rejected_foreign_instance"] == 1


@pytest.mark.asyncio
async def test_own_workspace_promoted(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="ws-own", own_inst="A")
    await c._process_message(b"m4", _msg())
    assert len(_promoted(c, "ws-own")) >= 1


@pytest.mark.asyncio
async def test_no_own_identity_configured_only_blank_rule(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch)
    await c._process_message(b"m5", _msg(workspace=b"anything"))
    assert len(_promoted(c, "anything")) >= 1


@pytest.mark.asyncio
async def test_consume_loop_acks_rejected_event(tmp_path, monkeypatch):
    """_process_message must not raise for rejected events, so start() acks them."""
    c = _consumer(tmp_path, monkeypatch, own_ws="ws-own")
    await c._process_message(b"m6", _msg(workspace=b"ws-other"))
    await c._process_message(b"m7", _msg(workspace=None))


# --- Continuation: real publisher/launcher shapes -------------------------

@pytest.mark.asyncio
async def test_basename_own_matches_absolute_path_event(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="dopemux-mvp", own_inst="ab12")
    await c._process_message(b"c1", _msg(workspace=b"/Users/x/code/dopemux-mvp/", instance=b"ab12"))
    assert len(_promoted(c, "/Users/x/code/dopemux-mvp/", "ab12")) >= 1


@pytest.mark.asyncio
async def test_basename_own_rejects_other_path(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="dopemux-mvp")
    await c._process_message(b"c2", _msg(workspace=b"/Users/x/code/other"))
    assert _promoted(c, "/Users/x/code/other") == []
    assert c.metrics["rejected_foreign_workspace"] == 1


@pytest.mark.asyncio
async def test_absolute_own_requires_exact_match(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="/Users/x/code/dopemux-mvp")
    await c._process_message(b"c3", _msg(workspace=b"/Users/y/code/dopemux-mvp"))
    assert c.metrics["rejected_foreign_workspace"] == 1
    await c._process_message(b"c4", _msg(workspace=b"/Users/x/code/dopemux-mvp"))
    assert len(_promoted(c, "/Users/x/code/dopemux-mvp")) >= 1


@pytest.mark.asyncio
async def test_same_basename_different_instance_rejected(tmp_path, monkeypatch):
    c = _consumer(tmp_path, monkeypatch, own_ws="dopemux-mvp", own_inst="ab12")
    await c._process_message(b"c5", _msg(workspace=b"/Users/x/code/dopemux-mvp", instance=b"zz99"))
    assert c.metrics["rejected_foreign_instance"] == 1
    assert _promoted(c, "/Users/x/code/dopemux-mvp", "zz99") == []
