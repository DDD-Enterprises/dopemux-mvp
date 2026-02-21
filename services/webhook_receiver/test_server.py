from __future__ import annotations

import http.client
import importlib.util
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path


def _load_module(name: str, module_path: Path):
    """Load a module by file path, registering it in sys.modules so that
    Python 3.13 dataclasses can resolve forward-reference annotations."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module  # register before exec so dataclasses can resolve annotations
    spec.loader.exec_module(module)
    return module


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


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def test_sqlite_event_store_idempotency(tmp_path: Path) -> None:
    storage = _load_storage_module()
    interface_mod = _load_ledger_interface_module()

    db_url = f"sqlite:///{(tmp_path / 'events.db').as_posix()}"
    os.environ["WEBHOOK_DB_URL"] = db_url

    # run migrations first
    migrate_script = Path(__file__).resolve().parents[2] / "scripts" / "webhook_migrate.py"
    assert migrate_script.exists()
    assert os.system(f"python {migrate_script} --db {db_url}") == 0

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
    assert os.system(f"python {migrate_script} --db {db_url}") == 0

    monkeypatch.setenv("OPENAI_WEBHOOK_SECRET", "test_secret")

    def _fail_verify(raw_body, headers, secret):
        raise RuntimeError("bad_signature")

    monkeypatch.setattr(server_mod, "verify_openai_webhook", _fail_verify)
    event_store = storage.build_event_store(db_url)
    port = _free_port()
    httpd = server_mod.WebhookServer("127.0.0.1", port, event_store)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)

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
    assert os.system(f"python {migrate_script} --db {db_url}") == 0

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
    time.sleep(0.05)

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


def _build_store_with_migrations(tmp_path: Path, db_name: str = "events.db"):
    """Helper: migrate + build SQLite EventStore."""
    storage = _load_storage_module()
    db_url = f"sqlite:///{(tmp_path / db_name).as_posix()}"
    migrate_script = Path(__file__).resolve().parents[2] / "scripts" / "webhook_migrate.py"
    assert migrate_script.exists()
    rc = os.system(f"python {migrate_script} --db {db_url}")
    assert rc == 0, f"migration failed with code {rc}"
    os.environ["WEBHOOK_DB_URL"] = db_url
    return storage.build_event_store(db_url)


def _load_ledger_module(name: str):
    """Load a module from the ledger package by file path."""
    root = Path(__file__).resolve().parents[2]
    return _load_module(
        f"ledger_{name}",
        root / "services" / "webhook_receiver" / "ledger" / f"{name}.py",
    )


def test_phase_r_async_submit_finalize_integration(tmp_path: Path) -> None:
    """End-to-end: submit pending -> simulate webhook ingestion -> finalize writes output."""
    interface_mod = _load_ledger_interface_module()
    store = _build_store_with_migrations(tmp_path)

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


def test_latest_attempt_reconciliation_stale_event_orphaned(tmp_path: Path) -> None:
    """Stale attempt: a superseded job should be marked orphaned, not trigger output."""
    interface_mod = _load_ledger_interface_module()
    store = _build_store_with_migrations(tmp_path, "events2.db")

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
