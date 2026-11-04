"""REST write routes: omitted ids, workspace binding, auth modes, principal, health."""

from __future__ import annotations

import logging
import sqlite3

import httpx
import pytest

from .helpers import fake_token, load_dope_memory_auth_identity, write_hash_file

auth_identity = load_dope_memory_auth_identity()

BOUND = "ws-bound"

# Minimal valid bodies (without the identity fields) for every mutating route.
WRITE_ROUTES = {
    "memory_store": {"category": "implementation", "entry_type": "decision", "summary": "s"},
    "memory_correct": {"entry_id": "missing", "correction_type": "summary"},
    "memory_link_resolution": {"issue_entry_id": "a", "resolution_entry_id": "b"},
    "memory_generate_reflection": {},
    "memory_mark_issue": {"issue_entry_id": "a", "description": "d"},
}


@pytest.fixture()
def make_client(monkeypatch, ledger_path, tmp_path):
    import dope_memory_main as dm

    clients = []

    def factory(mode="log", tokens=None, bound=BOUND):
        auth_dir = tmp_path / "auth"
        if tokens is not None:
            write_hash_file(auth_dir, tokens)
        gate = auth_identity.AuthGate(mode=mode, auth_dir=auth_dir)
        monkeypatch.setattr(dm, "AUTH_GATE", gate)
        monkeypatch.setattr(dm, "BOUND_WORKSPACE_ID", bound)
        monkeypatch.setattr(
            dm, "mcp_server", dm.DopeMemoryMCPServer(workspace_id=bound or "x", instance_id="A")
        )
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=dm.app), base_url="http://test"
        )
        clients.append(client)
        return client, gate

    yield factory


def _principals(ledger_path) -> list[str]:
    if not ledger_path.exists():
        return []
    conn = sqlite3.connect(str(ledger_path))
    try:
        return [r[0] for r in conn.execute("SELECT write_principal FROM work_log_entries")]
    finally:
        conn.close()


def _body(route, **ids):
    return {**WRITE_ROUTES[route], **ids}


IDS = {"workspace_id": BOUND, "instance_id": "inst-1"}


@pytest.mark.parametrize("route", sorted(WRITE_ROUTES))
@pytest.mark.parametrize("missing", ["workspace_id", "instance_id"])
async def test_should_not_reject_write_without_an_id_schema_wise(make_client, route, missing):
    # Amendment 04 (W12): an omitted id is filled from the binding, so the request
    # model no longer answers 422 for it. (Fill behaviour: tests/unit/runner_memory_2a_r2_w12.)
    client, _ = make_client()
    ids = {k: v for k, v in IDS.items() if k != missing}
    resp = await client.post(f"/tools/{route}", json=_body(route, **ids))
    assert resp.status_code != 422


@pytest.mark.parametrize("omitted", [("workspace_id",), ("instance_id",), ("workspace_id", "instance_id")])
async def test_should_store_a_write_with_omitted_ids_under_the_binding(make_client, ledger_path, omitted):
    client, _ = make_client()
    ids = {k: v for k, v in IDS.items() if k not in omitted}
    resp = await client.post("/tools/memory_store", json=_body("memory_store", **ids))
    assert resp.status_code == 200, resp.text
    assert resp.json()["created"] is True
    assert _principals(ledger_path) == ["unverified"]


@pytest.mark.parametrize("route", sorted(WRITE_ROUTES))
async def test_should_treat_blank_ids_as_omitted(make_client, route):
    client, _ = make_client()
    resp = await client.post(
        f"/tools/{route}", json=_body(route, workspace_id=" ", instance_id=" ")
    )
    assert resp.status_code != 422
    assert "workspace_id" not in resp.text or "required" not in resp.text


@pytest.mark.parametrize("route", sorted(WRITE_ROUTES))
async def test_should_reject_workspace_that_differs_from_binding(make_client, route, ledger_path):
    client, _ = make_client()
    resp = await client.post(
        f"/tools/{route}", json=_body(route, workspace_id="someone-else", instance_id="inst-1")
    )
    assert resp.status_code == 400
    assert "bound" in resp.text
    assert _principals(ledger_path) == []


async def test_should_reject_writes_when_server_has_no_workspace_binding(make_client):
    client, _ = make_client(bound=None)
    resp = await client.post("/tools/memory_store", json=_body("memory_store", **IDS))
    assert resp.status_code == 400
    assert "DOPE_MEMORY_WORKSPACE_ID" in resp.text


async def test_should_store_write_and_principal_for_valid_token(make_client, ledger_path):
    token = fake_token()
    client, _ = make_client("enforce", {token: "runner:codex"})
    resp = await client.post(
        "/tools/memory_store",
        json=_body("memory_store", **IDS),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["created"] is True
    assert _principals(ledger_path) == ["runner:codex"]


@pytest.mark.parametrize(
    "mode,kind,status,principal",
    [
        ("off", "valid", 200, "unverified"),
        ("off", "invalid", 200, "unverified"),
        ("off", "missing", 200, "unverified"),
        ("log", "valid", 200, "runner:codex"),
        ("log", "invalid", 200, "unverified"),
        ("log", "missing", 200, "unverified"),
        ("enforce", "valid", 200, "runner:codex"),
        ("enforce", "invalid", 401, None),
        ("enforce", "missing", 401, None),
    ],
)
async def test_should_apply_auth_mode_to_rest_writes(
    make_client, ledger_path, mode, kind, status, principal
):
    token = fake_token()
    client, _ = make_client(mode, {token: "runner:codex"})
    headers = {
        "valid": {"Authorization": f"Bearer {token}"},
        "invalid": {"Authorization": f"Bearer {fake_token('bad')}"},
        "missing": {},
    }[kind]
    resp = await client.post("/tools/memory_store", json=_body("memory_store", **IDS), headers=headers)
    assert resp.status_code == status, resp.text
    if status == 401:
        assert resp.headers["www-authenticate"].lower().startswith("bearer")
        assert _principals(ledger_path) == []
    else:
        assert _principals(ledger_path) == [principal]


async def test_should_return_401_before_validating_ids_in_enforce(make_client):
    client, _ = make_client("enforce", {fake_token(): "runner:codex"})
    resp = await client.post("/tools/memory_store", json={"category": "x"})
    assert resp.status_code == 401


async def test_should_leave_reads_open_in_enforce(make_client):
    client, _ = make_client("enforce", {fake_token(): "runner:codex"})
    resp = await client.post("/tools/memory_search", json={"query": "anything"})
    assert resp.status_code == 200
    resp = await client.post("/tools/memory_recap", json={})
    assert resp.status_code == 200


async def test_should_count_unverified_rest_callers_in_health(make_client):
    client, _ = make_client("log", {fake_token(): "runner:codex"})
    await client.post(
        "/tools/memory_store", json=_body("memory_store", **IDS), headers={"User-Agent": "curl/8.4"}
    )
    health = (await client.get("/health")).json()
    assert health["auth_unverified_calls"] == {"curl/8.4": 1}


@pytest.mark.parametrize("mode", ["off", "log", "enforce"])
async def test_should_report_auth_fields_on_health(make_client, mode):
    client, _ = make_client(mode, {fake_token(): "runner:codex"})
    health = (await client.get("/health")).json()
    assert health["status"] == "healthy"
    assert health["auth_mode"] == mode
    assert health["identity_required_writes"] is True
    assert health["auth_hash_file"] == "ok"


async def test_should_not_log_authorization_header_on_rejected_write(make_client, caplog):
    token = fake_token("leak")
    client, _ = make_client("enforce", {fake_token(): "runner:codex"})
    with caplog.at_level(logging.DEBUG):
        resp = await client.post(
            "/tools/memory_store",
            json=_body("memory_store", **IDS),
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401
    assert token not in caplog.text and token not in resp.text
