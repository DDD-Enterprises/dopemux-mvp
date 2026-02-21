from __future__ import annotations

import importlib.util
import sqlite3
import threading
import urllib.error
import urllib.request
from pathlib import Path


def _load_server_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "services" / "webhook_receiver" / "server.py"
    spec = importlib.util.spec_from_file_location("webhook_receiver_server", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _openai_event(server, *, delivery_id: str, attempt: int = 1):
    return server.ProviderEvent(
        provider="openai",
        delivery_id=delivery_id,
        event_id=f"evt_{delivery_id}",
        event_type="response.completed",
        payload={
            "id": f"evt_{delivery_id}",
            "type": "response.completed",
            "data": {
                "id": "resp_123",
                "metadata": {
                    "run_id": "run_1",
                    "phase": "D",
                    "step_id": "D2",
                    "partition_id": "D_P0001",
                    "attempt": attempt,
                },
            },
        },
        headers={"webhook-id": delivery_id},
        external_id="resp_123",
        run_id="run_1",
        phase="D",
        step_id="D2",
        partition_id="D_P0001",
        attempt=attempt,
    )


def test_provider_events_idempotent_insert(tmp_path: Path) -> None:
    server = _load_server_module()
    db_path = tmp_path / "events.db"
    server.init_db(db_path)
    event = _openai_event(server, delivery_id="wh_1", attempt=1)

    first = server.ingest_provider_event(db_path, event)
    second = server.ingest_provider_event(db_path, event)

    assert first is True
    assert second is False
    with sqlite3.connect(db_path) as conn:
        provider_count = conn.execute("select count(*) from provider_events").fetchone()[0]
        run_event_count = conn.execute("select count(*) from run_events").fetchone()[0]
    assert provider_count == 1
    assert run_event_count == 1


def test_async_job_latest_attempt_marks_orphaned(tmp_path: Path) -> None:
    server = _load_server_module()
    db_path = tmp_path / "events.db"
    server.init_db(db_path)
    server.register_async_job(
        db_path,
        job_id="job_attempt_1",
        provider="openai",
        job_kind="responses.background",
        external_job_id="resp_123",
        run_id="run_1",
        phase="D",
        step_id="D2",
        partition_id="D_P0001",
        attempt=1,
        status="running",
    )
    server.register_async_job(
        db_path,
        job_id="job_attempt_2",
        provider="openai",
        job_kind="responses.background",
        external_job_id="resp_123",
        run_id="run_1",
        phase="D",
        step_id="D2",
        partition_id="D_P0001",
        attempt=2,
        status="running",
    )
    stale_event = _openai_event(server, delivery_id="wh_stale", attempt=1)
    server.ingest_provider_event(db_path, stale_event)
    latest_event = _openai_event(server, delivery_id="wh_latest", attempt=2)
    server.ingest_provider_event(db_path, latest_event)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "select delivery_id, orphaned from provider_events p join run_events r on p.id=r.provider_event_id order by p.id"
        ).fetchall()
    assert rows[0][0] == "wh_stale"
    assert rows[0][1] == 1
    assert rows[1][0] == "wh_latest"
    assert rows[1][1] == 0


def test_poller_ingest_is_idempotent(tmp_path: Path) -> None:
    server = _load_server_module()
    db_path = tmp_path / "events.db"
    server.init_db(db_path)
    server.register_async_job(
        db_path,
        job_id="job_xai_1",
        provider="xai",
        job_kind="batch",
        external_job_id="xjob_001",
        run_id="run_2",
        phase="C",
        step_id="C0",
        partition_id="C_P0001",
        attempt=1,
        status="running",
    )
    jobs = server.list_pending_jobs(db_path, ["xai"])
    assert len(jobs) == 1
    inserted_first = server.ingest_polled_job_event(db_path, jobs[0], "completed")
    inserted_second = server.ingest_polled_job_event(db_path, jobs[0], "completed")
    assert inserted_first is True
    assert inserted_second is False

    with sqlite3.connect(db_path) as conn:
        provider_count = conn.execute("select count(*) from provider_events where provider='xai'").fetchone()[0]
        status = conn.execute("select status from async_jobs where job_id='job_xai_1'").fetchone()[0]
    assert provider_count == 1
    assert status == "completed"


def _start_server(server_module, db_path: Path):
    srv = server_module.WebhookServer("127.0.0.1", 0, db_path)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    return srv, thread


def test_http_invalid_signature_returns_unauthorized(tmp_path: Path, monkeypatch) -> None:
    server = _load_server_module()
    db_path = tmp_path / "events.db"
    server.init_db(db_path)
    monkeypatch.setenv("OPENAI_WEBHOOK_SECRET", "test-secret")
    srv, thread = _start_server(server, db_path)
    try:
        url = f"http://127.0.0.1:{srv.server_port}/webhook/openai"
        req = urllib.request.Request(
            url,
            data=b'{"id":"evt_bad","type":"response.completed"}',
            method="POST",
            headers={"Content-Type": "application/json", "webhook-id": "wh_bad"},
        )
        try:
            urllib.request.urlopen(req, timeout=5)
            assert False, "Expected HTTPError for invalid signature"
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


def test_http_duplicate_delivery_returns_no_content(tmp_path: Path, monkeypatch) -> None:
    server = _load_server_module()
    db_path = tmp_path / "events.db"
    server.init_db(db_path)
    monkeypatch.setenv("OPENAI_WEBHOOK_SECRET", "test-secret")

    class _FakeAdapter:
        def __init__(self, secret: str):
            assert secret == "test-secret"

        def verify_and_normalize(self, raw_body: bytes, headers: dict):
            delivery_id = (
                headers.get("webhook-id")
                or headers.get("Webhook-Id")
                or headers.get("X-Webhook-Id")
                or ""
            )
            return server.ProviderEvent(
                provider="openai",
                delivery_id=str(delivery_id),
                event_id="evt_http_ok",
                event_type="response.completed",
                payload={
                    "id": "evt_http_ok",
                    "type": "response.completed",
                    "data": {"id": "resp_http_ok", "metadata": {"run_id": "run_http"}},
                },
                headers={str(k): str(v) for k, v in headers.items()},
                external_id="resp_http_ok",
                run_id="run_http",
                phase="",
                step_id="",
                partition_id="",
                attempt=None,
            )

    monkeypatch.setattr(server, "OpenAIWebhookAdapter", _FakeAdapter)
    srv, thread = _start_server(server, db_path)
    try:
        url = f"http://127.0.0.1:{srv.server_port}/webhook/openai"
        headers = {"Content-Type": "application/json", "webhook-id": "wh_dup_http"}
        req1 = urllib.request.Request(url, data=b"{}", method="POST", headers=headers)
        req2 = urllib.request.Request(url, data=b"{}", method="POST", headers=headers)
        with urllib.request.urlopen(req1, timeout=5) as resp1:
            assert resp1.status == 204
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            assert resp2.status == 204
        with sqlite3.connect(db_path) as conn:
            count = conn.execute(
                "select count(*) from provider_events where provider='openai' and delivery_id='wh_dup_http'"
            ).fetchone()[0]
        assert count == 1
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)
