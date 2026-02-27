from __future__ import annotations

import http.client
import importlib.util
import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


def _load_module(name: str, module_path: Path):
    """Load a module by file path, registering it in sys.modules so that
    Python 3.13 dataclasses can resolve forward-reference annotations."""
    if name in sys.modules:
        return sys.modules[name]

    # Temporarily adjust sys.path so that absolute imports within the loaded
    # module (e.g. `from ledger.interface ...`) resolve against this service
    # rather than an unrelated third-party package.
    old_sys_path = list(sys.path)
    try:
        module_dir = str(module_path.parent)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

        # Also add the webhook_receiver service root (containing the `ledger`
        # package) if we can locate it by walking up from the module path.
        service_root = module_path.parent
        while service_root.parent != service_root and service_root.name != "webhook_receiver":
            service_root = service_root.parent
        if service_root.name == "webhook_receiver":
            service_root_str = str(service_root)
            if service_root_str not in sys.path:
                sys.path.insert(0, service_root_str)

        spec = importlib.util.spec_from_file_location(name, module_path)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        # Register before exec so dataclasses can resolve annotations.
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path = old_sys_path
def _load_server_module():
    root = Path(__file__).resolve().parents[2]
    return _load_module(
        "webhook_receiver_server",
        root / "services" / "webhook_receiver" / "server.py",
    )


def _load_storage_module():
    root = Path(__file__).resolve().parents[2]
    return _load_module(
        "webhook_receiver_storage",
        root / "services" / "webhook_receiver" / "storage.py",
    )


def _load_ledger_interface_module():
    root = Path(__file__).resolve().parents[2]
    return _load_module(
        "webhook_receiver_ledger_interface",
        root / "services" / "webhook_receiver" / "ledger" / "interface.py",
    )


def _load_poller_module():
    root = Path(__file__).resolve().parents[2]
    return _load_module(
        "webhook_receiver_poller",
        root / "services" / "webhook_receiver" / "poller.py",
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _wait_for_server(host: str, port: int, max_attempts: int = 50, delay: float = 0.1) -> None:
    """Wait until the server is accepting connections, up to max_attempts tries."""
    for _ in range(max_attempts):
        try:
            with socket.create_connection((host, port), timeout=delay):
                return
        except (ConnectionRefusedError, OSError):
            time.sleep(delay)
    raise TimeoutError(f"Server on {host}:{port} did not become ready after {max_attempts} attempts")


def test_sqlite_event_store_idempotency(tmp_path: Path, monkeypatch) -> None:
    storage = _load_storage_module()
    interface_mod = _load_ledger_interface_module()

    db_url = f"sqlite:///{(tmp_path / 'events.db').as_posix()}"
    monkeypatch.setenv("WEBHOOK_DB_URL", db_url)

    # run migrations first
    migrate_script = Path(__file__).resolve().parents[2] / "scripts" / "webhook_migrate.py"
    assert migrate_script.exists()
    subprocess.run([sys.executable, str(migrate_script), "--db", db_url], check=True)

    store = storage.build_event_store(db_url)
    payload = {"id": "evt_abc", "type": "response.completed", "data": {"id": "resp_1"}}
    event = interface_mod.WebhookEventInsert(
        provider="openai",
        idempotency_key="wh_1",
        event_type="response.completed",
        event_id="evt_abc",
        received_at_utc="2026-02-21T00:00:00Z",
        payload_json=json.dumps(payload),
        headers_json=json.dumps({"webhook-id": "wh_1"}),
        signature_valid=True,
    )
    first = store.insert_webhook_event_if_absent(event)
    second = store.insert_webhook_event_if_absent(event)
    assert first is True
    assert second is False
    assert store.count_webhook_events() == 1


def test_server_invalid_signature_returns_401(tmp_path: Path, monkeypatch) -> None:
    server_mod = _load_server_module()
    storage = _load_storage_module()

    db_url = f"sqlite:///{(tmp_path / 'events.db').as_posix()}"
    migrate_script = Path(__file__).resolve().parents[2] / "scripts" / "webhook_migrate.py"
    subprocess.run([sys.executable, str(migrate_script), "--db", db_url], check=True)

    monkeypatch.setenv("OPENAI_WEBHOOK_SECRET", "test_secret")

    def _fail_verify(raw_body, headers, secret):
        raise RuntimeError("bad_signature")

    monkeypatch.setattr(server_mod, "verify_openai_webhook", _fail_verify)
    event_store = storage.build_event_store(db_url)
    port = _free_port()
    httpd = server_mod.WebhookServer("127.0.0.1", port, event_store)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    _wait_for_server("127.0.0.1", port)

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request(
        "POST",
        "/webhook/openai",
        body="{}",
        headers={"Content-Type": "application/json", "webhook-id": "wh_invalid"},
    )
    response = conn.getresponse()
    body = response.read().decode("utf-8")
    conn.close()
    httpd.shutdown()
    thread.join(timeout=1)

    assert response.status == 401
    assert "invalid_signature" in body


def test_server_duplicate_delivery_returns_204_and_no_second_insert(tmp_path: Path, monkeypatch) -> None:
    server_mod = _load_server_module()
    storage = _load_storage_module()

    db_url = f"sqlite:///{(tmp_path / 'events.db').as_posix()}"
    migrate_script = Path(__file__).resolve().parents[2] / "scripts" / "webhook_migrate.py"
    subprocess.run([sys.executable, str(migrate_script), "--db", db_url], check=True)

    monkeypatch.setenv("OPENAI_WEBHOOK_SECRET", "test_secret")

    payload = {
        "id": "evt_1",
        "type": "response.completed",
        "data": {
            "id": "resp_1",
            "metadata": {
                "run_id": "run_test",
                "phase": "R",
                "step_id": "R1",
                "partition_id": "R_P0001",
                "attempt": "1",
            },
        },
    }

    def _ok_verify(raw_body, headers, secret):
        return payload

    monkeypatch.setattr(server_mod, "verify_openai_webhook", _ok_verify)
    event_store = storage.build_event_store(db_url)
    port = _free_port()
    httpd = server_mod.WebhookServer("127.0.0.1", port, event_store)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    _wait_for_server("127.0.0.1", port)

    headers = {"Content-Type": "application/json", "webhook-id": "wh_dupe"}
    for _ in range(2):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("POST", "/webhook/openai", body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        _ = response.read()
        conn.close()
        assert response.status == 204

    httpd.shutdown()
    thread.join(timeout=1)

    assert event_store.count_webhook_events() == 1
    assert event_store.count_run_events() == 1


# --- TP-WEBHOOKS-0002 tests ---


def _build_store_with_migrations(tmp_path: Path, monkeypatch, db_name: str = "events.db"):
    """Helper: migrate + build SQLite EventStore."""
    storage = _load_storage_module()
    db_url = f"sqlite:///{(tmp_path / db_name).as_posix()}"
    migrate_script = Path(__file__).resolve().parents[2] / "scripts" / "webhook_migrate.py"
    assert migrate_script.exists()
    subprocess.run([sys.executable, str(migrate_script), "--db", db_url], check=True)
    monkeypatch.setenv("WEBHOOK_DB_URL", db_url)
    return storage.build_event_store(db_url)


def _load_ledger_module(name: str):
    """Load a module from the ledger package by file path."""
    root = Path(__file__).resolve().parents[2]
    return _load_module(
        f"ledger_{name}",
        root / "services" / "webhook_receiver" / "ledger" / f"{name}.py",
    )


def test_phase_r_async_submit_finalize_integration(tmp_path: Path, monkeypatch) -> None:
    """End-to-end: submit pending -> simulate webhook ingestion -> finalize writes output."""
    interface_mod = _load_ledger_interface_module()
    store = _build_store_with_migrations(tmp_path, monkeypatch)

    run_id = "run_test_async"
    step_id = "R1"
    partition_id = "R_P0001"
    attempt = 1
    external_job_id = "resp_async_001"

    # 1. Simulate submit: register async_job and run_event(request.pending)
    store.register_async_job(
        interface_mod.AsyncJobInsert(
            provider="openai",
            job_kind="responses_async",
            external_job_id=external_job_id,
            run_id=run_id,
            phase="R",
            step_id=step_id,
            partition_id=partition_id,
            attempt=attempt,
            status="submitted",
        )
    )
    import hashlib

    pending_dedupe = hashlib.sha256(
        f"openai|{run_id}|R|{step_id}|{partition_id}|{attempt}|request.pending".encode()
    ).hexdigest()
    store.append_run_event(
        interface_mod.RunEventInsert(
            run_id=run_id,
            phase="R",
            step_id=step_id,
            partition_id=partition_id,
            provider="openai",
            event_type="request.pending",
            event_id=None,
            provider_ref=external_job_id,
            webhook_event_id=None,
            dedupe_key=pending_dedupe,
            orphaned=False,
        )
    )

    # 2. Simulate webhook receiver storing the completion event
    webhook_payload = {
        "id": "evt_done_001",
        "type": "response.completed",
        "data": {
            "id": external_job_id,
            "metadata": {
                "run_id": run_id,
                "phase": "R",
                "step_id": step_id,
                "partition_id": partition_id,
                "attempt": str(attempt),
            },
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "artifacts": [
                                        {
                                            "artifact_name": "R_ARBITRATION.json",
                                            "payload": {"verdict": "pass"},
                                        }
                                    ]
                                }
                            ),
                        }
                    ],
                }
            ],
        },
    }
    inserted = store.insert_webhook_event_if_absent(
        interface_mod.WebhookEventInsert(
            provider="openai",
            idempotency_key="wh_done_001",
            event_type="response.completed",
            event_id="evt_done_001",
            received_at_utc="2026-02-21T00:00:00Z",
            payload_json=json.dumps(webhook_payload),
            headers_json=json.dumps({"webhook-id": "wh_done_001"}),
            signature_valid=True,
        )
    )
    assert inserted is True
    webhook_event_id = store.fetch_webhook_event_id("openai", "wh_done_001")
    assert webhook_event_id is not None

    # 3. Link completion run_event to the webhook_event
    completion_dedupe = hashlib.sha256(
        f"openai|{run_id}|R|{step_id}|{partition_id}|{attempt}|response.completed".encode()
    ).hexdigest()
    store.append_run_event(
        interface_mod.RunEventInsert(
            run_id=run_id,
            phase="R",
            step_id=step_id,
            partition_id=partition_id,
            provider="openai",
            event_type="response.completed",
            event_id="evt_done_001",
            provider_ref=external_job_id,
            webhook_event_id=webhook_event_id,
            dedupe_key=completion_dedupe,
            orphaned=False,
        )
    )

    # 4. Verify list_completed_provider_refs sees it
    completed = store.list_completed_provider_refs(provider="openai", run_id=run_id, phase="R")
    assert external_job_id in completed

    # 5. Verify pending_jobs sees the submitted job
    pending = store.list_pending_jobs(provider="openai", run_id=run_id, phase="R")
    assert len(pending) == 1
    assert pending[0]["external_job_id"] == external_job_id

    # 6. Simulate finalizer: mark as completed
    store.update_async_job_status(
        provider="openai",
        external_job_id=external_job_id,
        attempt=attempt,
        status="completed",
        last_error=None,
    )
    # Should no longer appear in pending
    still_pending = store.list_pending_jobs(provider="openai", run_id=run_id, phase="R")
    assert len(still_pending) == 0


def test_latest_attempt_reconciliation_stale_event_orphaned(tmp_path: Path, monkeypatch) -> None:
    """Stale attempt: a superseded job should be marked orphaned, not trigger output."""
    interface_mod = _load_ledger_interface_module()
    store = _build_store_with_migrations(tmp_path, monkeypatch, "events2.db")

    run_id = "run_stale"
    step_id = "R1"
    partition_id = "R_P0001"

    # Register two attempts for the same tuple
    for attempt in (1, 2):
        store.register_async_job(
            interface_mod.AsyncJobInsert(
                provider="openai",
                job_kind="responses_async",
                external_job_id=f"resp_{attempt}",
                run_id=run_id,
                phase="R",
                step_id=step_id,
                partition_id=partition_id,
                attempt=attempt,
                status="submitted",
            )
        )

    # Latest attempt should be 2
    latest = store.latest_attempt_for_tuple(
        run_id=run_id, phase="R", step_id=step_id, partition_id=partition_id
    )
    assert latest == 2

    # Attempt 1 is stale: mark orphaned
    store.update_async_job_status(
        provider="openai",
        external_job_id="resp_1",
        attempt=1,
        status="orphaned",
        last_error="stale_attempt",
    )

    # Attempt 2 is still pending
    pending = store.list_pending_jobs(provider="openai", run_id=run_id, phase="R")
    assert len(pending) == 1
    assert pending[0]["external_job_id"] == "resp_2"
    assert pending[0]["attempt"] == 2

    # find_async_job without attempt returns latest (attempt 2)
    job = store.find_async_job(provider="openai", external_job_id="resp_2")
    assert job is not None
    assert int(job["attempt"]) == 2

    # find_async_job for orphaned attempt 1
    orphaned_job = store.find_async_job(provider="openai", external_job_id="resp_1", attempt=1)
    assert orphaned_job is not None
    assert orphaned_job["status"] == "orphaned"


def test_migration_sql_parity_logical_schema() -> None:
    root = Path(__file__).resolve().parents[2]
    sqlite_sql = (
        root
        / "services"
        / "webhook_receiver"
        / "migrations"
        / "sqlite"
        / "001_init_webhook_ledger.sql"
    ).read_text(encoding="utf-8")
    postgres_sql = (
        root
        / "services"
        / "webhook_receiver"
        / "migrations"
        / "postgres"
        / "001_init_webhook_ledger.sql"
    ).read_text(encoding="utf-8")

    required_logical_tokens = [
        "CREATE TABLE IF NOT EXISTS webhook_events",
        "provider",
        "idempotency_key",
        "event_type",
        "event_id",
        "received_at_utc",
        "payload_json",
        "CREATE TABLE IF NOT EXISTS run_events",
        "run_id",
        "phase",
        "step_id",
        "partition_id",
        "provider_ref",
        "webhook_event_id",
        "dedupe_key",
        "CREATE TABLE IF NOT EXISTS async_jobs",
        "job_kind",
        "external_job_id",
        "attempt",
        "status",
        "last_error",
    ]
    for token in required_logical_tokens:
        assert token in sqlite_sql
        assert token in postgres_sql


def test_storage_selects_postgres_backend_without_connecting(monkeypatch) -> None:
    storage = _load_storage_module()
    monkeypatch.setenv("WEBHOOK_DB_URL", "postgresql://user:pass@localhost:5432/dopemux")
    event_store = storage.build_event_store()
    assert event_store.__class__.__name__ == "PostgresEventStore"


def test_poller_cycle_idempotent_for_terminal_status(tmp_path: Path, monkeypatch) -> None:
    interface_mod = _load_ledger_interface_module()
    poller = _load_poller_module()
    store = _build_store_with_migrations(tmp_path, monkeypatch, "poller.db")

    store.register_async_job(
        interface_mod.AsyncJobInsert(
            provider="xai",
            job_kind="responses_async",
            external_job_id="job_xai_1",
            run_id="run_poll",
            phase="R",
            step_id="R1",
            partition_id="R_P0001",
            attempt=1,
            status="submitted",
        )
    )

    first = poller.run_poll_cycle(store, ["xai"])
    second = poller.run_poll_cycle(store, ["xai"])

    assert first["jobs_seen"] == 1
    assert first["jobs_processed"] == 1
    assert first["events_inserted"] == 1
    assert second["events_inserted"] == 0
    assert store.count_webhook_events() == 1
    assert store.count_run_events() == 1


def test_poller_marks_stale_attempt_orphaned(tmp_path: Path, monkeypatch) -> None:
    interface_mod = _load_ledger_interface_module()
    poller = _load_poller_module()
    store = _build_store_with_migrations(tmp_path, monkeypatch, "poller_orphaned.db")

    # Two attempts for the same tuple: attempt=1 should be orphaned, attempt=2 should complete.
    store.register_async_job(
        interface_mod.AsyncJobInsert(
            provider="xai",
            job_kind="responses_async",
            external_job_id="job_xai_stale",
            run_id="run_orphan",
            phase="R",
            step_id="R1",
            partition_id="R_P0001",
            attempt=1,
            status="submitted",
        )
    )
    store.register_async_job(
        interface_mod.AsyncJobInsert(
            provider="xai",
            job_kind="responses_async",
            external_job_id="job_xai_latest",
            run_id="run_orphan",
            phase="R",
            step_id="R1",
            partition_id="R_P0001",
            attempt=2,
            status="submitted",
        )
    )

    result = poller.run_poll_cycle(store, ["xai"])
    assert result["events_inserted"] == 2

    stale_job = store.find_async_job(provider="xai", external_job_id="job_xai_stale", attempt=1)
    latest_job = store.find_async_job(provider="xai", external_job_id="job_xai_latest", attempt=2)
    assert stale_job is not None and stale_job["status"] == "orphaned"
    assert latest_job is not None and latest_job["status"] == "completed"


def test_poller_rejects_unsupported_provider() -> None:
    poller = _load_poller_module()
    try:
        poller._parse_provider_list("xai,unknown")
        assert False, "Expected ValueError for unsupported provider"
    except ValueError as exc:
        assert "Unsupported providers" in str(exc)
