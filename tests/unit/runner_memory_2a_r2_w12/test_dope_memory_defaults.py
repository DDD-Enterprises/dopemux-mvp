"""dope-memory: an omitted workspace_id / instance_id is filled from the server's own
binding (Amendment 04); a supplied workspace that is not the binding is still
rejected, and a server with no binding still rejects every write.

The backend is a recorder, so the tests see exactly which ids reach it.
"""

from __future__ import annotations

import httpx
import pytest

BOUND = "ws-bound"
SERVER_INSTANCE = "inst-server"

# route -> minimal valid body without the identity fields
WRITE_ROUTES = {
    "memory_store": {"category": "implementation", "entry_type": "decision", "summary": "s"},
    "memory_correct": {"entry_id": "e1", "correction_type": "summary"},
    "memory_link_resolution": {"issue_entry_id": "a", "resolution_entry_id": "b"},
    "memory_generate_reflection": {},
    "memory_mark_issue": {"issue_entry_id": "a", "description": "d"},
}
ROUTES = sorted(WRITE_ROUTES)


class Recorder:
    """Stands in for DopeMemoryMCPServer: records kwargs, always succeeds."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def __getattr__(self, name):
        if not name.startswith("memory_"):
            raise AttributeError(name)

        def call(**kwargs):
            import dope_memory_main as dm

            self.calls.append((name, kwargs))
            return dm.ToolResponse(success=True, data={"ok": True})

        return call


# --------------------------------------------------------------------------
# validate_write_ids
# --------------------------------------------------------------------------


def _auth():
    import auth_identity

    return auth_identity


@pytest.mark.parametrize("blank", [None, "", "   "])
def test_should_fill_an_omitted_or_blank_workspace_and_instance_from_the_binding(blank):
    resolved = _auth().validate_write_ids(blank, blank, BOUND, default_instance_id=SERVER_INSTANCE)
    assert resolved == (BOUND, SERVER_INSTANCE)


def test_should_default_the_instance_to_A_when_no_server_instance_is_given():
    assert _auth().validate_write_ids(None, None, BOUND) == (BOUND, "A")


def test_should_keep_supplied_matching_ids_unchanged():
    resolved = _auth().validate_write_ids(BOUND, "inst-caller", BOUND, default_instance_id=SERVER_INSTANCE)
    assert resolved == (BOUND, "inst-caller")


def test_should_still_reject_a_supplied_workspace_that_is_not_the_binding():
    with pytest.raises(_auth().WriteIdentityError, match="bound"):
        _auth().validate_write_ids("other", None, BOUND, default_instance_id=SERVER_INSTANCE)


@pytest.mark.parametrize("workspace", [None, "", BOUND, "other"])
@pytest.mark.parametrize("bound", [None, ""])
def test_should_reject_every_write_when_the_server_has_no_binding(workspace, bound):
    with pytest.raises(_auth().WriteIdentityError, match="DOPE_MEMORY_WORKSPACE_ID"):
        _auth().validate_write_ids(workspace, "i", bound)


# --------------------------------------------------------------------------
# REST
# --------------------------------------------------------------------------


@pytest.fixture()
def rest(monkeypatch, ledger_path):
    import auth_identity
    import dope_memory_main as dm

    recorder = Recorder()

    def factory(bound=BOUND):
        monkeypatch.setattr(dm, "AUTH_GATE", auth_identity.AuthGate(mode="log"))
        monkeypatch.setattr(dm, "BOUND_WORKSPACE_ID", bound)
        monkeypatch.setattr(dm, "DEFAULT_INSTANCE_ID", SERVER_INSTANCE)
        monkeypatch.setattr(dm, "mcp_server", recorder)
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=dm.app), base_url="http://test")
        return client, recorder

    return factory


@pytest.mark.parametrize("route", ROUTES)
async def test_should_fill_both_ids_on_a_rest_write_that_omits_them(rest, route):
    client, recorder = rest()
    resp = await client.post(f"/tools/{route}", json=WRITE_ROUTES[route])
    assert resp.status_code == 200, resp.text
    ((name, kwargs),) = recorder.calls
    assert name == route
    assert (kwargs["workspace_id"], kwargs["instance_id"]) == (BOUND, SERVER_INSTANCE)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("blank", ["", "  "])
async def test_should_treat_blank_rest_ids_as_omitted(rest, route, blank):
    client, recorder = rest()
    body = {**WRITE_ROUTES[route], "workspace_id": blank, "instance_id": blank}
    resp = await client.post(f"/tools/{route}", json=body)
    assert resp.status_code == 200, resp.text
    ((_, kwargs),) = recorder.calls
    assert (kwargs["workspace_id"], kwargs["instance_id"]) == (BOUND, SERVER_INSTANCE)


@pytest.mark.parametrize("route", ROUTES)
async def test_should_keep_supplied_matching_rest_ids(rest, route):
    client, recorder = rest()
    body = {**WRITE_ROUTES[route], "workspace_id": BOUND, "instance_id": "inst-caller"}
    resp = await client.post(f"/tools/{route}", json=body)
    assert resp.status_code == 200, resp.text
    ((_, kwargs),) = recorder.calls
    assert (kwargs["workspace_id"], kwargs["instance_id"]) == (BOUND, "inst-caller")


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("instance", [None, "inst-caller"])
async def test_should_still_reject_a_mismatched_rest_workspace(rest, route, instance):
    client, recorder = rest()
    body = {**WRITE_ROUTES[route], "workspace_id": "someone-else"}
    if instance:
        body["instance_id"] = instance
    resp = await client.post(f"/tools/{route}", json=body)
    assert resp.status_code == 400
    assert "bound" in resp.text
    assert recorder.calls == []


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("workspace", [None, BOUND])
async def test_should_still_reject_every_rest_write_on_an_unbound_server(rest, route, workspace):
    client, recorder = rest(bound=None)
    body = dict(WRITE_ROUTES[route])
    if workspace:
        body["workspace_id"] = workspace
    resp = await client.post(f"/tools/{route}", json=body)
    assert resp.status_code == 400
    assert "DOPE_MEMORY_WORKSPACE_ID" in resp.text
    assert recorder.calls == []


def test_should_mark_the_ids_optional_on_every_rest_write_model():
    import dope_memory_main as dm

    schemas = dm.app.openapi()["components"]["schemas"]
    models = [
        "MemoryStoreRequest",
        "MemoryMarkIssueRequest",
        "MemoryLinkResolutionRequest",
        "MemoryCorrectRequest",
        "MemoryGenerateReflectionRequest",
    ]
    for name in models:
        required = set(schemas[name].get("required", []))
        assert not ({"workspace_id", "instance_id"} & required), name
        for field in ("workspace_id", "instance_id"):
            assert "binding" in schemas[name]["properties"][field].get("description", ""), (name, field)


def test_should_keep_identity_required_writes_true_on_health():
    import auth_identity

    assert auth_identity.AuthGate(mode="log").health_fields()["identity_required_writes"] is True


# --------------------------------------------------------------------------
# MCP
# --------------------------------------------------------------------------


@pytest.fixture()
def mcp_client():
    pytest.importorskip("fastmcp")
    import auth_identity
    import mcp_http
    from fastmcp import Client

    recorder = Recorder()

    def factory(bound=BOUND):
        server = mcp_http.build_mcp_server(
            lambda: recorder,
            bound_workspace_id=bound,
            read_default_instance_id=SERVER_INSTANCE,
            gate=auth_identity.AuthGate(mode="log"),
        )
        return Client(server), recorder

    return factory


@pytest.mark.parametrize("tool", ROUTES)
async def test_should_fill_both_ids_on_an_mcp_write_that_omits_them(mcp_client, tool):
    client, recorder = mcp_client()
    async with client:
        await client.call_tool(tool, WRITE_ROUTES[tool])
    ((name, kwargs),) = recorder.calls
    assert name == tool
    assert (kwargs["workspace_id"], kwargs["instance_id"]) == (BOUND, SERVER_INSTANCE)


@pytest.mark.parametrize("tool", ROUTES)
async def test_should_treat_blank_mcp_ids_as_omitted(mcp_client, tool):
    client, recorder = mcp_client()
    async with client:
        await client.call_tool(tool, {**WRITE_ROUTES[tool], "workspace_id": "", "instance_id": " "})
    ((_, kwargs),) = recorder.calls
    assert (kwargs["workspace_id"], kwargs["instance_id"]) == (BOUND, SERVER_INSTANCE)


@pytest.mark.parametrize("tool", ROUTES)
async def test_should_keep_supplied_matching_mcp_ids(mcp_client, tool):
    client, recorder = mcp_client()
    async with client:
        await client.call_tool(
            tool, {**WRITE_ROUTES[tool], "workspace_id": BOUND, "instance_id": "inst-caller"}
        )
    ((_, kwargs),) = recorder.calls
    assert (kwargs["workspace_id"], kwargs["instance_id"]) == (BOUND, "inst-caller")


@pytest.mark.parametrize("tool", ROUTES)
async def test_should_still_reject_a_mismatched_mcp_workspace(mcp_client, tool):
    from fastmcp.exceptions import ToolError

    client, recorder = mcp_client()
    async with client:
        with pytest.raises(ToolError, match="bound"):
            await client.call_tool(tool, {**WRITE_ROUTES[tool], "workspace_id": "other"})
    assert recorder.calls == []


@pytest.mark.parametrize("tool", ROUTES)
async def test_should_still_reject_every_mcp_write_on_an_unbound_server(mcp_client, tool):
    from fastmcp.exceptions import ToolError

    client, recorder = mcp_client(bound=None)
    async with client:
        with pytest.raises(ToolError, match="DOPE_MEMORY_WORKSPACE_ID"):
            await client.call_tool(tool, WRITE_ROUTES[tool])
        with pytest.raises(ToolError, match="DOPE_MEMORY_WORKSPACE_ID"):
            await client.call_tool(tool, {**WRITE_ROUTES[tool], "workspace_id": BOUND})
    assert recorder.calls == []


async def test_should_mark_the_ids_optional_with_a_binding_description_on_mcp_write_tools(mcp_client):
    client, _ = mcp_client()
    async with client:
        tools = {t.name: t.inputSchema for t in await client.list_tools()}
    for name in ROUTES:
        schema = tools[name]
        assert not ({"workspace_id", "instance_id"} & set(schema.get("required", []))), name
        for field in ("workspace_id", "instance_id"):
            assert "binding" in schema["properties"][field].get("description", ""), (name, field)
