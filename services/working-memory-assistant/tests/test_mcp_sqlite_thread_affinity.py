"""Real SQLite regression coverage across REST and streamable-HTTP MCP.

No backend/store doubles: the production REST handlers, lifespan, MCP transport,
auth gate and ChronicleStore all run in one ASGI event loop, as in the service.
Only service bindings/background integrations and ledger location are isolated.
"""

import asyncio
import hashlib
import json
import sqlite3

import httpx
import pytest
from fastapi import FastAPI

pytest.importorskip("fastmcp")
from fastmcp import Client  # noqa: E402
from fastmcp.client.transports import StreamableHttpTransport  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402

import dope_memory_main as dm  # noqa: E402
import mcp_http  # noqa: E402
from auth_identity import AuthGate, HASH_FILE_NAME, WriteAuthMiddleware  # noqa: E402

WORKSPACE = "sqlite-affinity-test"
INSTANCE = "A"
PRINCIPAL = "runner:sqlite-test"
# Public synthetic fixture; never a service/operator credential.
TOKEN = "example-sqlite-affinity-fixture-token"
IDS = {"workspace_id": WORKSPACE, "instance_id": INSTANCE}


def _entry(summary, **extra):
    return {
        "category": "implementation",
        "entry_type": "decision",
        "summary": summary,
        "session_id": "affinity-session",
        **extra,
    }


class Service:
    def __init__(self, app, ledger):
        self.app = app
        self.ledger = ledger
        self._lifespan = app.router.lifespan_context(app)

    async def __aenter__(self):
        await self._lifespan.__aenter__()
        return self

    async def __aexit__(self, *exc):
        try:
            return await self._lifespan.__aexit__(*exc)
        finally:
            # Production lifespan does not close cached stores. The fixture
            # owns its temporary connections and closes them after shutdown.
            if dm.mcp_server is not None:
                for store in dm.mcp_server._stores.values():
                    store.close()

    def rest_client(self):
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    def mcp_client(self):
        def factory(headers=None, timeout=None, auth=None, **kwargs):
            return httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app),
                headers=headers,
                timeout=timeout,
                auth=auth,
                follow_redirects=True,
            )

        return Client(
            StreamableHttpTransport(
                "http://test/mcp",
                headers={"Authorization": f"Bearer {TOKEN}"},
                httpx_client_factory=factory,
            )
        )

    def rows(self):
        with sqlite3.connect(self.ledger) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(
                "SELECT * FROM work_log_entries ORDER BY summary"
            )]


@pytest.fixture
def service(tmp_path, monkeypatch):
    ledger = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    (auth_dir / HASH_FILE_NAME).write_text(json.dumps({
        hashlib.sha256(TOKEN.encode()).hexdigest(): PRINCIPAL,
    }))
    gate = AuthGate(mode="log", auth_dir=auth_dir)
    for key, value in {
        "BOUND_WORKSPACE_ID": WORKSPACE,
        "DEFAULT_WORKSPACE_ID": WORKSPACE,
        "DEFAULT_INSTANCE_ID": INSTANCE,
        "AUTH_GATE": gate,
        "ENABLE_EVENTBUS": False,
        "ENABLE_RETENTION_JOB": False,
        "ENABLE_MIRROR_SYNC": False,
        "ADHD_RECAP_ENABLED": False,
        "eventbus_consumer": None,
        "eventbus_task": None,
        "retention_task": None,
        "mirror_sync": None,
        "mirror_sync_task": None,
        "mcp_server": None,
    }.items():
        monkeypatch.setattr(dm, key, value)

    server = mcp_http.build_mcp_server(
        lambda: dm.mcp_server,
        bound_workspace_id=WORKSPACE,
        read_default_instance_id=INSTANCE,
        gate=gate,
    )
    mcp_app = mcp_http.build_mcp_http_app(server)
    old_mcp_app = dm.mcp_http_app
    monkeypatch.setattr(dm, "mcp_http_app", mcp_app)
    # Reuse actual REST route objects; replace only import-time MCP bindings.
    app = FastAPI(
        routes=[route for route in dm.app.routes
                if getattr(route, "app", None) is not old_mcp_app],
        lifespan=dm.lifespan,
    )
    app.add_middleware(WriteAuthMiddleware, get_gate=lambda: gate)
    app.mount("", mcp_app)
    return Service(app, ledger)


@pytest.mark.asyncio
async def test_rest_first_then_mcp_uses_same_sqlite_connection(service):
    async with service:
        async with service.rest_client() as rest:
            initial = await rest.post("/tools/memory_search", json=IDS)
            assert initial.status_code == 200, initial.text
            assert initial.json()["items"] == []
            store = next(iter(dm.mcp_server._stores.values()))
            connection = store.connect()
            async with service.mcp_client() as client:
                found = await client.call_tool("memory_search", {})
                assert found.data["items"] == []
                stored = await client.call_tool("memory_store", _entry("REST first"))
                assert stored.data["created"] is True
                found = await client.call_tool("memory_search", {"query": "REST first"})
                assert [row["id"] for row in found.data["items"]] == [stored.data["entry_id"]]
            found = await rest.post("/tools/memory_search", json={**IDS, "query": "REST first"})
            assert found.status_code == 200, found.text
            assert len(found.json()["items"]) == 1
            assert store.connect() is connection
        rows = service.rows()
        assert len(rows) == 1
        assert rows[0]["write_principal"] == PRINCIPAL
        assert rows[0]["write_principal_self_asserted"] == 0


@pytest.mark.asyncio
async def test_mcp_first_then_rest_uses_same_sqlite_connection(service):
    async with service:
        async with service.mcp_client() as client:
            stored = await client.call_tool("memory_store", _entry("MCP first"))
            async with service.rest_client() as rest:
                found = await rest.post("/tools/memory_search", json={**IDS, "query": "MCP first"})
                assert found.status_code == 200, found.text
                assert [row["id"] for row in found.json()["items"]] == [stored.data["entry_id"]]
                stored_rest = await rest.post("/tools/memory_store", json=_entry("REST second", **IDS))
                assert stored_rest.status_code == 200, stored_rest.text
            found = await client.call_tool("memory_search", {"query": "REST second"})
            assert [row["id"] for row in found.data["items"]] == [stored_rest.json()["entry_id"]]
        assert [(row["write_principal"], row["write_principal_self_asserted"])
                for row in service.rows()] == [(PRINCIPAL, 0), (PRINCIPAL, 0)]


@pytest.mark.asyncio
async def test_two_mcp_clients_share_real_sqlite_and_preserve_identity_scope(service):
    async with service:
        async with service.rest_client() as rest:
            assert (await rest.post("/tools/memory_search", json=IDS)).status_code == 200
            async with service.mcp_client() as first, service.mcp_client() as second:
                stored = await asyncio.gather(
                    first.call_tool("memory_store", _entry("client A")),
                    second.call_tool("memory_store", _entry("client B", instance_id="B")),
                )
                assert len({result.data["entry_id"] for result in stored}) == 2
                found_a, found_b = await asyncio.gather(
                    first.call_tool("memory_search", {"query": "client"}),
                    second.call_tool("memory_search", {"query": "client", "instance_id": "B"}),
                )
                assert [row["summary"] for row in found_a.data["items"]] == ["client A"]
                assert [row["summary"] for row in found_b.data["items"]] == ["client B"]
                # Explicit instance ids remain supported; workspace escape is denied.
                with pytest.raises(ToolError, match="bound workspace"):
                    await first.call_tool("memory_store", _entry("forbidden", workspace_id="other"))
            denied = await rest.post("/tools/memory_store", json=_entry("forbidden", workspace_id="other"))
            assert denied.status_code == 400
        assert [(row["instance_id"], row["write_principal"], row["write_principal_self_asserted"])
                for row in service.rows()] == [("A", PRINCIPAL, 0), ("B", PRINCIPAL, 0)]


@pytest.mark.asyncio
async def test_cancelled_client_cleans_transport_without_extra_write(service):
    tasks_before = set(asyncio.all_tasks())
    async with service:
        written = asyncio.Event()
        client = service.mcp_client()

        async def client_session():
            async with client:
                await client.call_tool("memory_store", _entry("before cancellation"))
                written.set()
                await asyncio.Event().wait()

        task = asyncio.create_task(client_session())
        try:
            await asyncio.wait_for(written.wait(), timeout=10)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert not client.is_connected()
        async with service.mcp_client() as next_client:
            found = await next_client.call_tool("memory_search", {"query": "before cancellation"})
            assert len(found.data["items"]) == 1
        assert not next_client.is_connected()
        assert len(service.rows()) == 1
        connection = next(iter(dm.mcp_server._stores.values())).connect()
    # sse-starlette keeps one process/loop shutdown watcher beyond app lifespan.
    # Session/client tasks must be gone; the test owns cleanup of that watcher.
    await asyncio.sleep(0)
    pending = [task for task in asyncio.all_tasks() - tasks_before if not task.done()]
    assert len(pending) <= 1
    for task in pending:
        assert task.get_coro().__qualname__ == "_shutdown_watcher"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT 1")


@pytest.mark.asyncio
async def test_other_memory_callbacks_share_rest_initialized_sqlite(service):
    async with service:
        async with service.rest_client() as rest:
            assert (await rest.post("/tools/memory_search", json=IDS)).status_code == 200
        async with service.mcp_client() as client:
            # Empty recap/reflection still exercise their real SQLite paths.
            recap = await client.call_tool("memory_recap", {})
            assert recap.data["cards"] == []
            reflection = await client.call_tool("memory_generate_reflection", {})
            assert reflection.data["reflection_id"] is None
            reflections = await client.call_tool("memory_reflections", {})
            assert reflections.data == {"reflections": [], "count": 0}
            trajectory = await client.call_tool("memory_trajectory", {})
            assert trajectory.data["current_stream"] == "idle"
            stored = await client.call_tool("memory_store", _entry("issue entry"))
            resolution = await client.call_tool("memory_store", _entry("resolution entry"))
            issue_id = stored.data["entry_id"]
            marked = await client.call_tool("memory_mark_issue", {
                "issue_entry_id": issue_id, "description": "test issue",
            })
            assert marked.data == {"issue_marked": True}
            linked = await client.call_tool("memory_link_resolution", {
                "issue_entry_id": issue_id,
                "resolution_entry_id": resolution.data["entry_id"],
            })
            assert linked.data == {"linked": True}
            corrected = await client.call_tool("memory_correct", {
                "entry_id": issue_id,
                "correction_type": "summary",
                "corrected_summary": "corrected issue",
                "idempotency_key": "sqlite-affinity-correction",
            })
            assert corrected.data["superseded_entry_id"] == issue_id
            replay = await client.call_tool("memory_replay_session", {
                "session_id": "affinity-session", "mode": "replay_full", "top_k": 10,
            })
            assert {row["summary"] for row in replay.data["items"]} == {
                "issue entry", "corrected issue", "resolution entry",
            }
