"""ConPort: an omitted workspace_id / instance_id is filled from the server's own
binding (Amendment 04); a supplied workspace that is not the binding, a path and
body workspace that disagree, and an unbound server are still rejected.

Runs against the W02 fake pool; nothing touches a database or a network.
"""

from __future__ import annotations

from urllib.parse import quote

import pytest

from ..runner_memory_2a_r2_w02.helpers import BOUND_WORKSPACE as WS
from ..runner_memory_2a_r2_w02.helpers import INSTANCE, OTHER_WORKSPACE
from .conftest import load_conport_module, rest_client

PROGRESS_ID = "22222222-2222-2222-2222-222222222222"
SERVER_INSTANCE = "inst-server"

# name -> (method, path, body without any identity field, table that carries an instance)
CASES = {
    "context": ("POST", f"/api/context/{quote(WS, safe='')}", {"active_context": "x"}),
    "decision": ("POST", "/api/decisions", {"summary": "s", "rationale": "r"}),
    "progress": ("POST", "/api/progress", {"description": "do it"}),
    "progress_update": ("PUT", f"/api/progress/{PROGRESS_ID}", {"status": "COMPLETED"}),
    "custom_data": ("POST", "/api/custom_data", {"category": "c", "key": "k", "value": {"a": 1}}),
    "claim": ("POST", "/api/custom_data/claim",
              {"category": "c", "key": "k", "value": {"_fingerprint_v1": "x"}}),
    "delete": ("DELETE", "/api/custom_data?category=c&key=k", None),
    "fork": ("POST", "/api/instance/fork", {"target_instance": INSTANCE}),
    "promote": ("POST", "/api/progress/promote", {"progress_id": PROGRESS_ID}),
    "promote_all": ("POST", "/api/progress/promote_all", {}),
}
# Cases whose workspace comes from the body or query (the context path carries it).
BODY_WS = [n for n in CASES if n != "context"]
# Cases that need an instance to be a real one (never "shared").
NEEDS_REAL_INSTANCE = {"promote_all"}


async def _call(client, name, *, body="default", path=None):
    method, default_path, default_body = CASES[name]
    payload = default_body if body == "default" else body
    kwargs = {}
    if payload is not None and method != "DELETE":
        kwargs["json"] = payload
    return await client.request(method, path or default_path, **kwargs)


def _stored(server):
    return server.db_pool.writes()


# Writes keyed by row id (or by instance) never carry the workspace as an argument;
# for them the proof that the workspace was filled is the 200 (the ownership check
# compares the row's workspace with the resolved one) and the write itself.
ID_KEYED = {"progress_update": "UPDATE progress_entries", "promote": "UPDATE progress_entries",
            "conport_update_progress": "UPDATE progress_entries", "conport_promote": "UPDATE progress_entries"}


def _assert_filled_with_the_binding(server, name):
    if name in ID_KEYED:
        assert server.db_pool.write_sql(ID_KEYED[name]), name
    elif name not in ("promote_all", "conport_promote_all"):
        assert any(WS in args for _, args in _stored(server)), name


# --------------------------------------------------------------------------
# validate_write_ids
# --------------------------------------------------------------------------


@pytest.fixture()
def conport_auth():
    return load_conport_module("auth_identity")


@pytest.mark.parametrize("blank", [None, "", "   "])
def test_should_fill_an_omitted_or_blank_workspace_from_the_binding(conport_auth, blank):
    assert conport_auth.validate_write_ids(blank, "i", WS) == (WS, "i")


@pytest.mark.parametrize("blank", [None, "", "  "])
def test_should_fill_an_omitted_instance_from_the_server_default(conport_auth, blank):
    assert conport_auth.validate_write_ids(WS, blank, WS, default_instance_id=SERVER_INSTANCE) == (
        WS, SERVER_INSTANCE)
    assert conport_auth.validate_write_ids(WS, blank, WS, default_instance_id="shared") == (WS, "shared")


def test_should_keep_supplied_matching_ids_unchanged(conport_auth):
    resolved = conport_auth.validate_write_ids(WS, "inst-caller", WS, default_instance_id=SERVER_INSTANCE)
    assert resolved == (WS, "inst-caller")


def test_should_still_reject_a_supplied_workspace_that_is_not_the_binding(conport_auth):
    with pytest.raises(conport_auth.WriteIdentityError, match="does not match"):
        conport_auth.validate_write_ids(OTHER_WORKSPACE, "i", WS)


@pytest.mark.parametrize("workspace", [None, "", WS, OTHER_WORKSPACE])
@pytest.mark.parametrize("bound", [None, ""])
def test_should_reject_every_write_when_the_server_has_no_binding(conport_auth, workspace, bound):
    with pytest.raises(conport_auth.WriteIdentityError, match="no workspace binding"):
        conport_auth.validate_write_ids(workspace, "i", bound)


def test_should_keep_requiring_an_instance_when_no_default_is_offered(conport_auth):
    """fork_instance names its target, so it passes no default."""
    with pytest.raises(conport_auth.WriteIdentityError, match="instance_id is required"):
        conport_auth.validate_write_ids(WS, None, WS)
    assert conport_auth.validate_write_ids(WS, None, WS, require_instance=False) == (WS, None)


def test_should_keep_identity_required_writes_true(conport_auth):
    assert conport_auth.AuthGate("log").health_fields()["identity_required_writes"] is True


# --------------------------------------------------------------------------
# REST
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", [n for n in CASES if n not in NEEDS_REAL_INSTANCE])
async def test_should_fill_an_omitted_workspace_id_from_the_binding(make_rest_server, name):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await _call(client, name)
        assert response.status == 200, await response.text()
    assert _stored(server), name
    _assert_filled_with_the_binding(server, name)


@pytest.mark.parametrize("name", BODY_WS)
@pytest.mark.parametrize("blank", ["", "   "])
async def test_should_treat_a_blank_workspace_id_as_omitted(make_rest_server, name, monkeypatch, blank):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    method, path, body = CASES[name]
    async with rest_client(server) as client:
        if name == "delete":
            response = await client.delete(f"/api/custom_data?workspace_id={blank}&category=c&key=k")
        else:
            response = await _call(client, name, body={**body, "workspace_id": blank})
        assert response.status == 200, await response.text()
    _assert_filled_with_the_binding(server, name)


async def test_should_fill_an_omitted_workspace_id_on_the_context_path_body(make_rest_server):
    """The path names the workspace; a blank body workspace is omitted, not a disagreement."""
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await _call(client, "context", body={"active_context": "x", "workspace_id": ""})
        assert response.status == 200, await response.text()


@pytest.mark.parametrize("name", [n for n in BODY_WS])
async def test_should_still_reject_a_supplied_workspace_that_is_not_the_binding_on_rest(
    make_rest_server, name, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    method, path, body = CASES[name]
    async with rest_client(server) as client:
        if name == "delete":
            response = await client.delete(
                f"/api/custom_data?workspace_id={OTHER_WORKSPACE}&category=c&key=k")
        else:
            response = await _call(client, name, body={**body, "workspace_id": OTHER_WORKSPACE})
        assert response.status == 400
        assert "does not match" in await response.text()
    assert _stored(server) == []


@pytest.mark.parametrize("name", ["progress_update", "promote"])
async def test_should_still_reject_an_entry_of_another_workspace_when_the_workspace_is_omitted(
    make_rest_server, name
):
    server = make_rest_server("off", progress_workspace=OTHER_WORKSPACE)
    async with rest_client(server) as client:
        response = await _call(client, name)  # no workspace_id: filled with the binding
        assert response.status == 400
        assert "different workspace" in await response.text()
    assert _stored(server) == []


async def test_should_still_reject_a_path_workspace_that_is_not_the_binding(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await _call(client, "context", path=f"/api/context/{quote(OTHER_WORKSPACE, safe='')}")
        assert response.status == 400
    assert _stored(server) == []


async def test_should_still_reject_a_path_and_body_workspace_that_disagree(make_rest_server):
    server = make_rest_server("off")
    async with rest_client(server) as client:
        response = await _call(client, "context", body={"active_context": "x", "workspace_id": OTHER_WORKSPACE})
        assert response.status == 400
    assert _stored(server) == []


@pytest.mark.parametrize("name", list(CASES))
@pytest.mark.parametrize("supplied", [False, True])
async def test_should_still_reject_every_rest_write_on_an_unbound_server(
    make_rest_server, name, supplied, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off", bound_workspace=None)
    method, path, body = CASES[name]
    async with rest_client(server) as client:
        if name == "delete":
            query = f"workspace_id={WS}&" if supplied else ""
            response = await client.delete(f"/api/custom_data?{query}category=c&key=k")
        else:
            payload = {**body, "workspace_id": WS} if supplied else body
            response = await _call(client, name, body=payload)
        assert response.status == 400
        assert "no workspace binding" in await response.text()
    assert _stored(server) == []


# -- instance fallback: server instance, then shared (NULL) ----------------------------


async def _post_progress(client, **extra):
    return await client.post("/api/progress", json={"description": "d", **extra})


async def test_should_fall_back_to_the_servers_instance_for_an_omitted_instance_id(
    make_rest_server, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        omitted = await _post_progress(client)
        blank = await _post_progress(client, instance_id="  ")
        supplied = await _post_progress(client, instance_id="inst-caller")
        shared = await _post_progress(client, instance_id="shared")
        assert {r.status for r in (omitted, blank, supplied, shared)} == {200}
    rows = server.db_pool.write_sql("INSERT INTO progress_entries")
    assert [args[9] for _, args in rows] == [SERVER_INSTANCE, SERVER_INSTANCE, "inst-caller", None]


async def test_should_fall_back_to_shared_when_the_server_has_no_instance(make_rest_server, monkeypatch):
    monkeypatch.delenv("DOPEMUX_INSTANCE_ID", raising=False)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        assert (await _post_progress(client)).status == 200
    ((_, args),) = server.db_pool.write_sql("INSERT INTO progress_entries")
    assert args[9] is None  # shared lands where NULL lands


async def test_should_fall_back_the_same_way_on_context_and_decisions(make_rest_server, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        assert (await _call(client, "context")).status == 200
        assert (await _call(client, "decision")).status == 200
    ((_, ctx),) = server.db_pool.write_sql("UPDATE workspace_contexts")
    assert ctx[6] == SERVER_INSTANCE
    ((_, decision),) = server.db_pool.write_sql("INSERT INTO decisions")
    assert SERVER_INSTANCE in decision


async def test_should_promote_all_for_the_servers_instance_and_refuse_shared(make_rest_server, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        ok = await _call(client, "promote_all")
        assert ok.status == 200, await ok.text()
    monkeypatch.delenv("DOPEMUX_INSTANCE_ID")
    server = make_rest_server("off")
    async with rest_client(server) as client:
        refused = await _call(client, "promote_all")
        assert refused.status == 400
        assert "real instance" in await refused.text()


async def test_should_keep_fork_target_instance_required(make_rest_server, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)  # must NOT stand in for the target
    server = make_rest_server("off")
    async with rest_client(server) as client:
        for body in ({}, {"target_instance": "shared"}, {"workspace_id": WS}):
            response = await client.post("/api/instance/fork", json=body)
            assert response.status == 400, body
        ok = await client.post("/api/instance/fork", json={"target_instance": INSTANCE})
        assert ok.status == 200
    assert all(SERVER_INSTANCE not in args for _, args in _stored(server))


# -- the REST /mcp surface ---------------------------------------------------------------


def _rpc(name, arguments):
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}


MCP_OMITTING = {
    "conport_update_context": {"active_context": "x"},
    "conport_log_decision": {"summary": "s", "rationale": "r"},
    "conport_log_progress": {"description": "d"},
    "conport_update_progress": {"progress_id": PROGRESS_ID, "status": "COMPLETED"},
    "conport_save_custom_data": {"category": "c", "key": "k", "value": {"a": 1}},
    "conport_delete_custom_data": {"category": "c", "key": "k"},
    "conport_fork_instance": {"target_instance": INSTANCE},
    "conport_promote": {"progress_id": PROGRESS_ID},
    "conport_promote_all": {},
}


@pytest.mark.parametrize("tool", list(MCP_OMITTING))
async def test_should_fill_omitted_ids_on_every_mcp_write_tool(make_rest_server, tool, monkeypatch):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        server.port = client.port  # the custom_data tools call back into the REST port
        body = await (await client.post("/mcp", json=_rpc(tool, MCP_OMITTING[tool]))).json()
    assert "error" not in body, (tool, body)
    _assert_filled_with_the_binding(server, tool)


@pytest.mark.parametrize("tool", list(MCP_OMITTING))
async def test_should_still_reject_a_mismatched_workspace_on_every_mcp_write_tool(
    make_rest_server, tool, monkeypatch
):
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", SERVER_INSTANCE)
    server = make_rest_server("off")
    async with rest_client(server) as client:
        server.port = client.port
        body = await (await client.post(
            "/mcp", json=_rpc(tool, {**MCP_OMITTING[tool], "workspace_id": OTHER_WORKSPACE}))).json()
    assert "error" in body, tool
    assert _stored(server) == []


async def test_should_list_the_rest_mcp_write_tools_with_optional_ids(make_rest_server):
    server = make_rest_server("off")
    write_tools = {
        "conport_update_context", "conport_log_decision", "conport_log_progress",
        "conport_update_progress", "conport_save_custom_data", "conport_delete_custom_data",
    }
    async with rest_client(server) as client:
        listing = await (await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})).json()
    tools = {t["name"]: t["inputSchema"] for t in listing["result"]["tools"]}
    for name in write_tools:
        schema = tools[name]
        assert "workspace_id" not in schema["required"], name
        assert "binding" in schema["properties"]["workspace_id"]["description"], name
    for name in ("conport_update_context", "conport_log_decision", "conport_log_progress",
                 "conport_update_progress"):
        assert "instance_id" not in tools[name]["required"], name
        assert "binding" in tools[name]["properties"]["instance_id"]["description"], name
    assert "instance_id" not in tools["conport_save_custom_data"]["properties"]
    for name in ("conport_get_context", "conport_get_decisions", "conport_get_progress", "conport_search_content"):
        assert "workspace_id" in tools[name]["required"], name  # reads keep requiring it
