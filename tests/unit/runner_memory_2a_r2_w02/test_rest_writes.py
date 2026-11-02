"""ConPort REST port (enhanced_server.py): ids per table, ``shared``, the binding
check, the three auth modes, the stored principal and the /mcp write tools.

The server runs against a fake pool and fake Redis; nothing touches a network
except the aiohttp test client talking to the in-process app.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import pytest

from .conftest import rest_client
from .helpers import BOUND_WORKSPACE, INSTANCE, OTHER_WORKSPACE, fake_token

PROGRESS_ID = "22222222-2222-2222-2222-222222222222"
WS = BOUND_WORKSPACE


def _ids(**extra):
    return {"workspace_id": WS, "instance_id": INSTANCE, **extra}


# name, method, path, body, table, requires_instance
CASES = {
    "context": ("POST", f"/api/context/{quote(WS, safe='')}", {"active_context": "x", "instance_id": INSTANCE},
                "workspace_contexts", True),
    "decision": ("POST", "/api/decisions", {"workspace_id": WS, "summary": "s", "rationale": "r"},
                 "decisions", False),
    "progress": ("POST", "/api/progress", _ids(description="do it"), "progress_entries", True),
    "progress_update": ("PUT", f"/api/progress/{PROGRESS_ID}", _ids(status="COMPLETED"),
                        "progress_entries", True),
    "custom_data": ("POST", "/api/custom_data",
                    {"workspace_id": WS, "category": "c", "key": "k", "value": {"a": 1}},
                    "custom_data", False),
    "claim": ("POST", "/api/custom_data/claim",
              {"workspace_id": WS, "category": "c", "key": "k", "value": {"_fingerprint_v1": "x"}},
              "custom_data", False),
    "delete": ("DELETE", f"/api/custom_data?workspace_id={WS}&category=c&key=k", None,
               "custom_data", False),
    "fork": ("POST", "/api/instance/fork", {"workspace_id": WS, "target_instance": INSTANCE},
             "progress_entries", True),
    "promote": ("POST", "/api/progress/promote", _ids(progress_id=PROGRESS_ID),
                "progress_entries", True),
    "promote_all": ("POST", "/api/progress/promote_all", _ids(), "progress_entries", True),
}
IDS = list(CASES)


async def _call(client, name, *, body=None, headers=None, path=None):
    method, default_path, default_body, _, _ = CASES[name]
    kwargs = {"headers": headers or {}}
    payload = default_body if body is None else body
    if payload is not None and method != "DELETE":
        kwargs["json"] = payload
    return await client.request(method, path or default_path, **kwargs)


def _drop(body, key):
    return {k: v for k, v in body.items() if k != key}


# -- ids per table -------------------------------------------------------------


@pytest.mark.parametrize("name", IDS)
async def test_should_accept_a_write_with_bound_ids(make_rest_server, name):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await _call(client, name)
        assert response.status == 200, await response.text()


@pytest.mark.parametrize("name", [n for n in IDS if n not in ("context", "delete")])
async def test_should_fill_an_omitted_workspace_id_on_body_writes(make_rest_server, name):
    # Amendment 04 (W12): an omitted workspace_id is the server's binding.
    server = make_rest_server("off")
    body = _drop(CASES[name][2], "workspace_id")
    async with rest_client(server) as client:
        response = await _call(client, name, body=body)
        assert response.status == 200, await response.text()
    assert server.db_pool.writes() != []


async def test_should_fill_an_omitted_workspace_id_on_delete_and_reject_the_wrong_one(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        omitted = await client.delete("/api/custom_data?category=c&key=k")
        assert omitted.status == 200, await omitted.text()
        assert any(args[:1] == (WS,) for _, args in server.db_pool.writes())
        before = len(server.db_pool.writes())
        wrong = await client.delete(f"/api/custom_data?workspace_id={OTHER_WORKSPACE}&category=c&key=k")
        assert wrong.status == 400
    assert len(server.db_pool.writes()) == before


@pytest.mark.parametrize("name", IDS)
async def test_should_reject_a_workspace_that_is_not_the_servers_binding(make_rest_server, name):
    server = make_rest_server("off")
    method, path, body, _, _ = CASES[name]
    if name == "context":
        path = f"/api/context/{quote(OTHER_WORKSPACE, safe='')}"
    elif name == "delete":
        path = f"/api/custom_data?workspace_id={OTHER_WORKSPACE}&category=c&key=k"
    else:
        body = {**body, "workspace_id": OTHER_WORKSPACE}
    async with rest_client(server) as client:
        response = await _call(client, name, body=body, path=path)
        assert response.status == 400
        assert "does not match" in (await response.text())
    assert server.db_pool.writes() == []


@pytest.mark.parametrize("name", [n for n in IDS if CASES[n][4] and n not in ("fork", "promote_all")])
async def test_should_fall_back_to_shared_for_an_omitted_instance_id(make_rest_server, name, monkeypatch):
    # Amendment 04 (W12): an omitted instance_id is the server's DOPEMUX_INSTANCE_ID, else shared (NULL).
    monkeypatch.delenv("DOPEMUX_INSTANCE_ID", raising=False)
    server = make_rest_server("off")
    body = _drop(CASES[name][2], "instance_id")
    async with rest_client(server) as client:
        response = await _call(client, name, body=body)
        assert response.status == 200, await response.text()
    assert server.db_pool.writes() != []


async def test_should_refuse_promote_all_when_the_instance_falls_back_to_shared(make_rest_server, monkeypatch):
    monkeypatch.delenv("DOPEMUX_INSTANCE_ID", raising=False)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await _call(client, "promote_all", body=_drop(CASES["promote_all"][2], "instance_id"))
        assert response.status == 400
        assert "real instance" in await response.text()
    assert server.db_pool.writes() == []


async def test_should_require_a_target_instance_on_fork(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        for body in ({"workspace_id": WS}, {"workspace_id": WS, "target_instance": "shared"}):
            response = await client.post("/api/instance/fork", json=body)
            assert response.status == 400
        ok = await client.post("/api/instance/fork", json={"workspace_id": WS, "instance_id": INSTANCE})
        assert ok.status == 200


async def test_should_not_require_an_instance_for_decisions_and_custom_data(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        for name in ("decision", "custom_data", "claim", "delete"):
            assert (await _call(client, name)).status == 200, name


async def test_should_keep_the_decision_instance_in_created_by_instance(make_rest_server):
    server = make_rest_server("off")
    body = {"workspace_id": WS, "summary": "s", "rationale": "r", "instance_id": INSTANCE}
    async with rest_client(server) as client:
        assert (await client.post("/api/decisions", json=body)).status == 200
        assert (await client.post("/api/decisions", json={**body, "instance_id": "shared"})).status == 200
    first, second = server.db_pool.write_sql("INSERT INTO decisions")
    assert "created_by_instance" in first[0]
    assert INSTANCE in first[1] and None in second[1] and "shared" not in second[1]


async def test_should_reject_a_progress_entry_from_another_workspace(make_rest_server):
    server = make_rest_server("off", progress_workspace=OTHER_WORKSPACE)
    async with rest_client(server) as client:
        for name in ("progress_update", "promote"):
            response = await _call(client, name)
            assert response.status == 400, name
            assert "workspace" in (await response.text())
    assert server.db_pool.writes() == []


# -- shared ------------------------------------------------------------------


async def test_should_store_shared_where_null_lands(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        shared = await client.post("/api/progress", json=_ids(description="a", instance_id="shared"))
        local = await client.post("/api/progress", json=_ids(description="b"))
        assert shared.status == 200 and local.status == 200
    shared_sql, local_sql = server.db_pool.write_sql("INSERT INTO progress_entries")
    assert shared_sql[1][9] is None  # instance_id column
    assert local_sql[1][9] == INSTANCE
    assert all("shared" not in args for _, args in server.db_pool.writes())


async def test_should_match_shared_context_rows_with_null(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await client.post(
            f"/api/context/{quote(WS, safe='')}", json={"active_context": "x", "instance_id": "shared"}
        )
        assert response.status == 200
    (sql, args), = server.db_pool.write_sql("UPDATE workspace_contexts")
    assert args[6] is None  # the WHERE instance argument is NULL, not the string 'shared'


async def test_should_promote_all_only_for_a_real_instance(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await client.post("/api/progress/promote_all", json=_ids(instance_id="shared"))
        assert response.status == 400


# -- principal stored ---------------------------------------------------------------


@pytest.mark.parametrize("name", [n for n in IDS if n != "delete"])
async def test_should_store_the_verified_principal(make_rest_server, name):
    token = fake_token()
    server = make_rest_server("log", {token: "runner:codex"})
    async with rest_client(server) as client:
        response = await _call(client, name, headers={"Authorization": f"Bearer {token}"})
        assert response.status == 200, await response.text()
    stored = [args for sql, args in server.db_pool.writes() if "write_principal" in sql]
    assert stored, name
    assert all("runner:codex" in args for args in stored)


@pytest.mark.parametrize("name", ["decision", "progress", "custom_data"])
async def test_should_store_unverified_in_log_mode_without_a_token(make_rest_server, name):
    server = make_rest_server("log", {fake_token(): "runner:codex"})
    async with rest_client(server) as client:
        response = await _call(client, name, headers={"User-Agent": "curl/8"})
        assert response.status == 200
        health = await (await client.get("/health")).json()
    stored = [args for sql, args in server.db_pool.writes() if "write_principal" in sql]
    assert stored and all("unverified" in args for args in stored)
    assert health["auth_unverified_calls"] == {"curl/8": 1}


async def test_should_record_unverified_for_every_write_in_off_mode(make_rest_server):
    token = fake_token()
    server = make_rest_server("off", {token: "runner:codex"})
    async with rest_client(server) as client:
        assert (await _call(client, "progress", headers={"Authorization": f"Bearer {token}"})).status == 200
    stored = [args for sql, args in server.db_pool.writes() if "write_principal" in sql]
    assert stored and all("unverified" in args and "runner:codex" not in args for args in stored)


# -- the three modes --------------------------------------------------------------------


@pytest.mark.parametrize("name", IDS)
async def test_should_reject_unverified_writes_with_401_in_enforce_mode(make_rest_server, name):
    server = make_rest_server("enforce", {fake_token(): "runner:codex"})
    async with rest_client(server) as client:
        for headers in ({}, {"Authorization": "Bearer FAKE-not-a-token"}, {"Authorization": "Basic abc"}):
            response = await _call(client, name, headers=headers)
            assert response.status == 401, (name, headers)
            assert response.headers["WWW-Authenticate"] == "Bearer"
    assert server.db_pool.writes() == []


@pytest.mark.parametrize("name", IDS)
async def test_should_accept_verified_writes_in_enforce_mode(make_rest_server, name):
    token = fake_token()
    server = make_rest_server("enforce", {token: "runner:claude"})
    async with rest_client(server) as client:
        response = await _call(client, name, headers={"Authorization": f"Bearer {token}"})
        assert response.status == 200, await response.text()


async def test_should_fail_closed_in_enforce_mode_without_a_hash_file(make_rest_server):
    server = make_rest_server("enforce", write_hash_dir=False)
    async with rest_client(server) as client:
        response = await _call(client, "progress", headers={"Authorization": f"Bearer {fake_token()}"})
        assert response.status == 401
        health = await (await client.get("/health")).json()
    assert health["auth_hash_file"] == "unconfigured"


async def test_should_authenticate_before_validating_ids(make_rest_server):
    server = make_rest_server("enforce", {fake_token(): "runner:codex"})
    async with rest_client(server) as client:
        response = await client.post("/api/progress", json={"description": "no ids, no token"})
        assert response.status == 401


async def test_should_not_gate_reads_in_any_mode(make_rest_server):
    server = make_rest_server("enforce", {})
    async with rest_client(server) as client:
        assert (await client.get("/health")).status == 200
        assert (await client.get(f"/api/context/{quote(WS, safe='')}")).status == 200
        assert (await client.get(f"/api/custom_data?workspace_id={WS}")).status == 200


async def test_should_report_the_gate_fields_on_health(make_rest_server):
    server = make_rest_server("enforce", {})
    async with rest_client(server) as client:
        health = await (await client.get("/health")).json()
    assert health["auth_mode"] == "enforce"
    assert health["identity_required_writes"] is True
    assert health["auth_hash_file"] == "ok"
    assert health["auth_principal_column"] == "ok"
    assert health["auth_unverified_calls"] == {}


async def test_should_count_callers_forwarded_by_the_verified_bridge_proxy(make_rest_server):
    from .helpers import fake_token as ft

    proxy, other = ft("proxy"), ft("codex")
    server = make_rest_server("log", {proxy: "internal:bridge-proxy", other: "runner:codex"})
    async with rest_client(server) as client:
        await _call(client, "progress", headers={"Authorization": f"Bearer {proxy}",
                                                 "X-Dopemux-Unverified-Caller": "some-agent/1"})
        # the header from anyone else is not trusted as a verified signal
        await _call(client, "progress", headers={"Authorization": f"Bearer {other}",
                                                 "X-Dopemux-Unverified-Caller": "spoof/1"})
        health = await (await client.get("/health")).json()
    assert health["auth_unverified_calls"] == {"some-agent/1": 1}
    stored = [args for sql, args in server.db_pool.writes() if "write_principal" in sql]
    assert any("internal:bridge-proxy" in args for args in stored)


# -- no workspace binding ---------------------------------------------------------------------


async def test_should_reject_every_write_when_the_server_has_no_binding(make_rest_server):
    server = make_rest_server("off", bound_workspace=None)
    async with rest_client(server) as client:
        response = await _call(client, "progress")
        assert response.status == 400
        assert "no workspace binding" in await response.text()
        assert (await client.get(f"/api/context/{quote(WS, safe='')}")).status == 200  # reads unchanged


# -- /mcp write tools -------------------------------------------------------------------------

MCP_WRITES = {
    "conport_update_context": _ids(active_context="x"),
    "conport_log_decision": {"workspace_id": WS, "summary": "s", "rationale": "r"},
    "conport_log_progress": _ids(description="d"),
    "conport_update_progress": _ids(progress_id=PROGRESS_ID, status="COMPLETED"),
    "conport_save_custom_data": {"workspace_id": WS, "category": "c", "key": "k", "value": {"a": 1}},
    "conport_delete_custom_data": {"workspace_id": WS, "category": "c", "key": "k"},
    "conport_fork_instance": {"workspace_id": WS, "target_instance": INSTANCE},
    "conport_promote": _ids(progress_id=PROGRESS_ID),
    "conport_promote_all": _ids(),
}


def _rpc(name, arguments, rid=1):
    return {"jsonrpc": "2.0", "id": rid, "method": "tools/call", "params": {"name": name, "arguments": arguments}}


@pytest.mark.parametrize("tool", list(MCP_WRITES))
async def test_should_gate_every_mcp_write_tool_in_enforce_mode(make_rest_server, tool):
    token = fake_token()
    server = make_rest_server("enforce", {token: "runner:codex"})
    async with rest_client(server) as client:
        server.port = client.port  # the custom_data tools call back into the REST port
        denied = await client.post("/mcp", json=_rpc(tool, MCP_WRITES[tool]))
        assert denied.status == 401
        assert server.db_pool.writes() == []
        ok = await client.post("/mcp", json=_rpc(tool, MCP_WRITES[tool]),
                               headers={"Authorization": f"Bearer {token}"})
        assert ok.status == 200
        assert "error" not in await ok.json(), tool


@pytest.mark.parametrize("tool", list(MCP_WRITES))
async def test_should_bind_every_mcp_write_tool_to_the_servers_workspace(make_rest_server, tool, monkeypatch):
    # Amendment 04 (W12): an omitted workspace_id is filled; a different one is rejected.
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", INSTANCE)
    server = make_rest_server("off")
    omitted = {k: v for k, v in MCP_WRITES[tool].items() if k != "workspace_id"}
    wrong = {**omitted, "workspace_id": OTHER_WORKSPACE}
    async with rest_client(server) as client:
        server.port = client.port
        filled = await (await client.post("/mcp", json=_rpc(tool, omitted))).json()
        assert "error" not in filled, (tool, filled)
        written = len(server.db_pool.writes())
        rejected = await (await client.post("/mcp", json=_rpc(tool, wrong))).json()
    assert "does not match" in rejected["error"]["message"], tool
    assert len(server.db_pool.writes()) == written


async def test_should_store_the_principal_for_mcp_custom_data_through_the_loopback(make_rest_server):
    token = fake_token()
    server = make_rest_server("enforce", {token: "runner:codex"})
    async with rest_client(server) as client:
        server.port = client.port
        response = await client.post(
            "/mcp", json=_rpc("conport_save_custom_data", MCP_WRITES["conport_save_custom_data"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status == 200 and "error" not in await response.json()
    stored = [args for sql, args in server.db_pool.writes() if "INSERT INTO custom_data" in sql]
    assert stored and "runner:codex" in stored[0]


async def test_should_leave_mcp_discovery_and_reads_open_in_enforce_mode(make_rest_server):
    server = make_rest_server("enforce", {})
    async with rest_client(server) as client:
        listing = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        read = await client.post("/mcp", json=_rpc("conport_get_context", {"workspace_id": WS}))
        assert listing.status == 200 and read.status == 200


async def test_should_gate_direct_conport_method_calls(make_rest_server):
    server = make_rest_server("enforce", {})
    async with rest_client(server) as client:
        response = await client.post(
            "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "conport_log_progress", "params": _ids(description="d")}
        )
        assert response.status == 401


# -- migration 008 not applied --------------------------------------------------------------------


async def test_should_still_write_without_the_column_in_log_mode_and_say_so(make_rest_server, caplog):
    server = make_rest_server("log", principal_tables=())
    with caplog.at_level(logging.WARNING):
        async with rest_client(server) as client:
            assert (await _call(client, "progress")).status == 200
            health = await (await client.get("/health")).json()
    sql, _ = server.db_pool.write_sql("INSERT INTO progress_entries")[0]
    assert "write_principal" not in sql
    assert health["auth_principal_column"] == "missing"
    assert "migration 008" in caplog.text


async def test_should_reject_writes_in_enforce_mode_without_the_column(make_rest_server):
    token = fake_token()
    server = make_rest_server("enforce", {token: "runner:codex"}, principal_tables=())
    async with rest_client(server) as client:
        response = await _call(client, "progress", headers={"Authorization": f"Bearer {token}"})
        assert response.status == 503
        assert "migration 008" in await response.text()
    assert server.db_pool.writes() == []


async def test_should_report_a_partly_migrated_database(make_rest_server):
    server = make_rest_server("log", principal_tables=("decisions",))
    async with rest_client(server) as client:
        health = await (await client.get("/health")).json()
    assert health["auth_principal_column"] == "partial"


# -- secrets ------------------------------------------------------------------------------------------


async def test_should_not_log_tokens_or_authorization_headers(make_rest_server, caplog):
    token = fake_token()
    server = make_rest_server("enforce", {token: "runner:codex"})
    with caplog.at_level(logging.DEBUG):
        async with rest_client(server) as client:
            await _call(client, "progress", headers={"Authorization": f"Bearer {token}"})
            await _call(client, "progress", headers={"Authorization": f"Bearer {token}x"})
    assert token not in caplog.text and "Authorization" not in caplog.text and "Bearer" not in caplog.text
