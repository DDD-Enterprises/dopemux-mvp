"""Service-backed tools: enveloped, CANONICAL, redacted, fail-closed, profile-bound."""

from __future__ import annotations

from dcp_facade import envelope as E
from dcp_facade import tools


def _reg(build_registry, project_entry, ws, profiles):
    return build_registry(
        [project_entry(ws, project_id="p", service_profiles=profiles)],
        approved_roots=[str(ws.parent)],
    )


def test_search_decisions_ok_envelope(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, ft = make_client(json_body={"decisions": [{"id": "d1", "summary": "x"}], "count": 1})
    env = tools.search_decisions(reg, "p", limit=5, client=client)
    assert env["status"] == E.OK
    assert env["source_system"] == E.SOURCE_CONPORT
    assert env["authority_label"] == E.AUTHORITY_CANONICAL
    assert env["data"]["count"] == 1
    # workspace_id came from the registry profile, not the caller
    assert ft.last["params"]["workspace_id"] == "ws-test"


def test_search_decisions_query_is_deferred_not_routed_to_broken_search(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    # Phase 1: query mode must NOT hit the broken ConPort /api/search route.
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, ft = make_client(json_body={"results": {"decisions": []}})
    env = tools.search_decisions(reg, "p", query="oauth", client=client)
    assert env["status"] == E.PARTIAL
    assert env["data"] is None
    assert any("/api/search" in lim and "deferred" in lim for lim in env["limitations"])
    assert ft.calls == []  # backend never hit for a query


def test_search_chronicle_posts_with_topk_cap(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, ft = make_client(json_body={"items": []})
    env = tools.search_chronicle(reg, "p", query="x", top_k=99, client=client)
    assert env["status"] == E.OK
    assert env["source_system"] == E.SOURCE_DOPE_MEMORY
    assert ft.last["method"] == "POST"
    assert ft.last["json"]["top_k"] == 3


def test_replay_requires_session_id(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, _ = make_client()
    env = tools.replay_chronicle_session(reg, "p", session_id="", client=client)
    assert env["status"] == E.BLOCKED
    assert any("session_id is required" in r for r in env["blocked_reasons"])


def test_search_progress_fail_closed_without_readonly_flag(make_workspace, build_registry, project_entry, make_client):
    # conport profile WITHOUT progress_readonly_safe → blocked (auto-fork risk)
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, {"conport": {"base_url": "http://127.0.0.1:3004", "workspace_id": "w"}})
    client, ft = make_client(json_body={"progress": []})
    env = tools.search_progress(reg, "p", client=client)
    assert env["status"] == E.BLOCKED
    assert any("auto-fork" in r for r in env["blocked_reasons"])
    assert ft.calls == []  # never hit the backend


def test_search_progress_allowed_with_readonly_flag(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, ft = make_client(json_body={"progress": [], "count": 0})
    env = tools.search_progress(reg, "p", client=client)
    assert env["status"] == E.OK
    assert ft.last["url"].endswith("/api/progress")


def test_unknown_project_blocked(build_registry, make_client):
    reg = build_registry([])
    client, _ = make_client()
    env = tools.search_decisions(reg, "ghost", client=client)
    assert env["status"] == E.BLOCKED


def test_missing_profile_blocked(make_workspace, build_registry, project_entry, make_client):
    ws = make_workspace()["path"]
    # no conport profile bound
    reg = _reg(build_registry, project_entry, ws, {"dope_memory": {"base_url": "http://127.0.0.1:3020", "workspace_id": "w"}})
    client, _ = make_client()
    env = tools.search_decisions(reg, "p", client=client)
    assert env["status"] == E.BLOCKED
    assert any("conport not configured" in r for r in env["blocked_reasons"])


def test_backend_unavailable_fails_closed(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, _ = make_client(raise_exc=TimeoutError("down"))
    env = tools.search_progress(reg, "p", client=client)
    assert env["status"] == E.BLOCKED
    assert any("backend unavailable" in r for r in env["blocked_reasons"])


def test_non_2xx_is_partial(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    client, _ = make_client(status=503, json_body=None)
    env = tools.search_progress(reg, "p", client=client)
    assert env["status"] == E.PARTIAL
    assert any("status 503" in lim for lim in env["limitations"])


def test_backend_response_is_redacted(make_workspace, build_registry, project_entry, make_client, conport_dm_profiles):
    ws = make_workspace()["path"]
    reg = _reg(build_registry, project_entry, ws, conport_dm_profiles)
    leaky = {"items": [{"summary": "token: [REDACTED] at [LOCAL_PATH_REDACTED]"}]}
    client, _ = make_client(json_body=leaky)
    env = tools.search_chronicle(reg, "p", client=client)
    blob = str(env["data"])
    assert "supersecret12345" not in blob
    assert "[LOCAL_PATH_REDACTED]" not in blob
    assert env["redactions"]  # categories reported
