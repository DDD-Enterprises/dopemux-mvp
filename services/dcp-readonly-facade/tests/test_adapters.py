"""ConPort + dope-memory adapters: correct routes/params, caps, POST-read only."""

from __future__ import annotations

import pytest

from dcp_facade import conport, dope_memory
from dcp_facade.http_client import ReadOnlyHttpError

CONPORT = "http://127.0.0.1:3004"
DM = "http://127.0.0.1:3020"


# --- ConPort (GET only) ----------------------------------------------------


def test_conport_get_decisions_route_and_cap(make_client):
    client, ft = make_client(json_body={"decisions": []})
    conport.get_decisions(client, CONPORT, "ws-1", limit=999)
    assert ft.last["method"] == "GET"
    assert ft.last["url"].endswith("/api/decisions")
    assert ft.last["params"]["workspace_id"] == "ws-1"
    assert ft.last["params"]["limit"] == 20  # capped


def test_conport_get_progress_with_status(make_client):
    client, ft = make_client(json_body={"progress": []})
    conport.get_progress(client, CONPORT, "ws-1", status="IN_PROGRESS", limit=5)
    assert ft.last["url"].endswith("/api/progress")
    assert ft.last["params"]["status"] == "IN_PROGRESS"
    assert ft.last["params"]["limit"] == 5


def test_conport_search_workspace_in_path(make_client):
    client, ft = make_client(json_body={"results": {}})
    conport.search(client, CONPORT, "ws-9", "auth", "decisions")
    assert ft.last["url"].endswith("/api/search/ws-9")
    assert ft.last["params"] == {"q": "auth", "type": "decisions"}


def test_conport_search_rejects_path_in_workspace_id(make_client):
    client, _ = make_client()
    for bad_ws in ("../etc", "a/b", "ws/..%2f"):
        with pytest.raises(ReadOnlyHttpError):
            conport.search(client, CONPORT, bad_ws, "q", "decisions")


# --- dope-memory (POST-read allowlist only) --------------------------------


def test_dm_search_body_and_topk_cap(make_client):
    client, ft = make_client(json_body={"items": []})
    dope_memory.memory_search(client, DM, "ws-1", query="x", top_k=50)
    assert ft.last["method"] == "POST"
    assert ft.last["url"].endswith("/tools/memory_search")
    assert ft.last["json"]["top_k"] == 3  # hard cap
    assert ft.last["json"]["workspace_id"] == "ws-1"


def test_dm_replay_mode_validation(make_client):
    client, ft = make_client(json_body={"items": []})
    dope_memory.memory_replay_session(client, DM, "ws-1", "sess-1", mode="evil_mode", top_k=2)
    assert ft.last["url"].endswith("/tools/memory_replay_session")
    assert ft.last["json"]["mode"] == "replay_current"  # invalid mode coerced
    assert ft.last["json"]["session_id"] == "sess-1"


def test_dm_adapter_cannot_hit_correct_route(make_client):
    # The adapter only ever passes the two read paths to post_read; prove a
    # rogue path is rejected by the client even if attempted.
    client, _ = make_client()
    with pytest.raises(ReadOnlyHttpError):
        client.post_read(DM, "/tools/memory_correct", {}, dope_memory.DOPE_MEMORY_READ_PATHS)
