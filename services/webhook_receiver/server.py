#!/usr/bin/env python3
"""Webhook receiver sidecar with provider-agnostic event ledger."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from providers.base import ProviderEvent
from providers.openai_adapter import OpenAIWebhookAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("webhook_receiver")

DB_LOCK = threading.Lock()
ASYNC_JOB_STATES = {"submitted", "running", "completed", "failed"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def now_unix() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def db_path_from_env() -> Path:
    raw = os.getenv("WEBHOOK_DB_PATH", "/data/webhook_receiver.db").strip()
    return Path(raw)


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _dedupe_key(*parts: str) -> str:
    token = "|".join(str(part).strip() for part in parts)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        # Deprecated legacy table retained as one-packet compatibility fallback.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
              webhook_id TEXT PRIMARY KEY,
              event_id TEXT,
              event_type TEXT,
              created_at INTEGER,
              received_at_utc TEXT NOT NULL,
              payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS provider_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              provider TEXT NOT NULL,
              delivery_id TEXT NOT NULL,
              event_id TEXT,
              event_type TEXT,
              received_at_utc TEXT NOT NULL,
              created_at INTEGER NOT NULL,
              headers_json TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              dedupe_key TEXT NOT NULL UNIQUE,
              UNIQUE(provider, delivery_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT,
              phase TEXT,
              step_id TEXT,
              partition_id TEXT,
              provider TEXT NOT NULL,
              event_type TEXT,
              event_id TEXT,
              external_id TEXT,
              provider_event_id INTEGER,
              dedupe_key TEXT NOT NULL UNIQUE,
              orphaned INTEGER NOT NULL DEFAULT 0,
              created_at_utc TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS async_jobs (
              job_id TEXT PRIMARY KEY,
              provider TEXT NOT NULL,
              job_kind TEXT NOT NULL,
              external_job_id TEXT NOT NULL,
              run_id TEXT,
              phase TEXT,
              step_id TEXT,
              partition_id TEXT,
              attempt INTEGER NOT NULL DEFAULT 1,
              status TEXT NOT NULL,
              last_error TEXT,
              created_at_utc TEXT NOT NULL,
              updated_at_utc TEXT NOT NULL,
              UNIQUE(provider, external_job_id, attempt)
            )
            """
        )
        conn.commit()


def _payload_meta(payload: Dict[str, Any]) -> Dict[str, str]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "run_id": str(metadata.get("run_id") or ""),
        "phase": str(metadata.get("phase") or ""),
        "step_id": str(metadata.get("step_id") or ""),
        "partition_id": str(metadata.get("partition_id") or ""),
        "external_id": str(data.get("id") or ""),
    }


def register_async_job(
    path: Path,
    *,
    job_id: str,
    provider: str,
    job_kind: str,
    external_job_id: str,
    run_id: str = "",
    phase: str = "",
    step_id: str = "",
    partition_id: str = "",
    attempt: int = 1,
    status: str = "submitted",
    last_error: str = "",
) -> None:
    state = status if status in ASYNC_JOB_STATES else "submitted"
    now = now_iso()
    with DB_LOCK:
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                INSERT INTO async_jobs (
                  job_id, provider, job_kind, external_job_id, run_id, phase, step_id, partition_id,
                  attempt, status, last_error, created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  status=excluded.status,
                  last_error=excluded.last_error,
                  updated_at_utc=excluded.updated_at_utc
                """,
                (
                    job_id,
                    provider,
                    job_kind,
                    external_job_id,
                    run_id,
                    phase,
                    step_id,
                    partition_id,
                    max(1, int(attempt)),
                    state,
                    last_error,
                    now,
                    now,
                ),
            )
            conn.commit()


def _latest_attempt_for_tuple(
    conn: sqlite3.Connection,
    run_id: str,
    phase: str,
    step_id: str,
    partition_id: str,
) -> Optional[int]:
    row = conn.execute(
        """
        SELECT MAX(attempt)
        FROM async_jobs
        WHERE run_id=? AND phase=? AND step_id=? AND partition_id=?
        """,
        (run_id, phase, step_id, partition_id),
    ).fetchone()
    if not row:
        return None
    value = row[0]
    if value is None:
        return None
    return int(value)


def _event_matches_latest_attempt(conn: sqlite3.Connection, event: ProviderEvent) -> bool:
    if not (event.run_id and event.phase and event.step_id and event.partition_id):
        return True
    latest = _latest_attempt_for_tuple(conn, event.run_id, event.phase, event.step_id, event.partition_id)
    if latest is None:
        return True
    if event.attempt is None:
        return False
    return int(event.attempt) == int(latest)


def insert_provider_event(path: Path, event: ProviderEvent) -> Tuple[bool, Optional[int]]:
    dedupe = _dedupe_key(event.provider, event.delivery_id)
    created_at = now_unix()
    with DB_LOCK:
        with sqlite3.connect(path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO provider_events (
                      provider, delivery_id, event_id, event_type, received_at_utc, created_at,
                      headers_json, payload_json, dedupe_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.provider,
                        event.delivery_id,
                        event.event_id,
                        event.event_type,
                        now_iso(),
                        created_at,
                        _json_dumps(event.headers),
                        _json_dumps(event.payload),
                        dedupe,
                    ),
                )
            except sqlite3.IntegrityError:
                existing = conn.execute(
                    "SELECT id FROM provider_events WHERE provider=? AND delivery_id=?",
                    (event.provider, event.delivery_id),
                ).fetchone()
                return False, int(existing[0]) if existing and existing[0] is not None else None

            provider_event_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # One-packet fallback: keep legacy table populated for openai deliveries.
            if event.provider == "openai":
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO webhook_events (
                          webhook_id, event_id, event_type, created_at, received_at_utc, payload_json
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.delivery_id,
                            event.event_id,
                            event.event_type,
                            created_at,
                            now_iso(),
                            _json_dumps(event.payload),
                        ),
                    )
                except Exception:
                    pass
            conn.commit()
    return True, int(provider_event_id)


def insert_run_event(
    conn: sqlite3.Connection,
    *,
    event: ProviderEvent,
    provider_event_id: Optional[int],
    orphaned: int,
) -> None:
    dedupe = _dedupe_key(
        event.provider,
        event.delivery_id,
        event.event_type,
        event.event_id,
        event.external_id,
        event.run_id,
        event.phase,
        event.step_id,
        event.partition_id,
        str(orphaned),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO run_events (
          run_id, phase, step_id, partition_id, provider, event_type, event_id, external_id,
          provider_event_id, dedupe_key, orphaned, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.run_id,
            event.phase,
            event.step_id,
            event.partition_id,
            event.provider,
            event.event_type,
            event.event_id,
            event.external_id,
            provider_event_id,
            dedupe,
            int(orphaned),
            now_iso(),
        ),
    )


def ingest_provider_event(path: Path, event: ProviderEvent) -> bool:
    inserted, provider_event_id = insert_provider_event(path, event)
    with DB_LOCK:
        with sqlite3.connect(path) as conn:
            orphaned = 0
            if not _event_matches_latest_attempt(conn, event):
                orphaned = 1
            insert_run_event(conn, event=event, provider_event_id=provider_event_id, orphaned=orphaned)
            conn.commit()
    return inserted


def list_pending_jobs(path: Path, providers: Sequence[str]) -> List[Dict[str, Any]]:
    if not providers:
        return []
    placeholders = ",".join("?" for _ in providers)
    query = (
        "SELECT job_id, provider, job_kind, external_job_id, run_id, phase, step_id, partition_id, attempt, status "
        f"FROM async_jobs WHERE status IN ('submitted','running') AND provider IN ({placeholders})"
    )
    with DB_LOCK:
        with sqlite3.connect(path) as conn:
            rows = conn.execute(query, tuple(providers)).fetchall()
    payload: List[Dict[str, Any]] = []
    for row in rows:
        payload.append(
            {
                "job_id": str(row[0] or ""),
                "provider": str(row[1] or ""),
                "job_kind": str(row[2] or ""),
                "external_job_id": str(row[3] or ""),
                "run_id": str(row[4] or ""),
                "phase": str(row[5] or ""),
                "step_id": str(row[6] or ""),
                "partition_id": str(row[7] or ""),
                "attempt": int(row[8] or 1),
                "status": str(row[9] or ""),
            }
        )
    return payload


def update_async_job_status(path: Path, job_id: str, status: str, last_error: str = "") -> None:
    state = status if status in ASYNC_JOB_STATES else "running"
    with DB_LOCK:
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                UPDATE async_jobs
                SET status=?, last_error=?, updated_at_utc=?
                WHERE job_id=?
                """,
                (state, last_error, now_iso(), job_id),
            )
            conn.commit()


def ingest_polled_job_event(path: Path, job: Dict[str, Any], final_status: str) -> bool:
    external_id = str(job.get("external_job_id") or "")
    provider = str(job.get("provider") or "")
    event_type = f"job.{final_status}"
    delivery_id = f"poll:{provider}:{external_id}:{final_status}"
    payload = {
        "source": "poller",
        "provider": provider,
        "job_id": str(job.get("job_id") or ""),
        "external_job_id": external_id,
        "status": final_status,
    }
    event = ProviderEvent(
        provider=provider,
        delivery_id=delivery_id,
        event_id=delivery_id,
        event_type=event_type,
        payload=payload,
        headers={},
        external_id=external_id,
        run_id=str(job.get("run_id") or ""),
        phase=str(job.get("phase") or ""),
        step_id=str(job.get("step_id") or ""),
        partition_id=str(job.get("partition_id") or ""),
        attempt=int(job.get("attempt") or 1),
    )
    inserted = ingest_provider_event(path, event)
    update_async_job_status(path, str(job.get("job_id") or ""), "completed" if final_status == "completed" else "failed")
    return inserted


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "DopemuxWebhookReceiver/2.0"

    def _write_json(self, status: int, payload: Dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/healthz":
            self._write_json(HTTPStatus.OK, {"status": "ok", "schema": "DPMX_WEBHOOK_V2"})
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/webhook/openai":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        secret = os.getenv("OPENAI_WEBHOOK_SECRET", "").strip()
        if not secret:
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "missing_openai_webhook_secret"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
        except Exception:
            content_length = 0
        raw_body = self.rfile.read(max(0, content_length))
        headers = {str(k): str(v) for k, v in self.headers.items()}
        adapter = OpenAIWebhookAdapter(secret=secret)
        try:
            event = adapter.verify_and_normalize(raw_body, headers)
        except Exception as exc:
            reason = str(exc)
            if "missing_webhook_id" in reason:
                self._write_json(HTTPStatus.BAD_REQUEST, {"error": "missing_webhook_id"})
                return
            logger.warning("provider=openai verify_failed reason=%s", reason)
            self._write_json(HTTPStatus.UNAUTHORIZED, {"error": "invalid_signature"})
            return

        inserted = ingest_provider_event(self.server.db_path, event)
        logger.info(
            "provider=%s delivery_id=%s event_type=%s event_id=%s status=%s",
            event.provider,
            event.delivery_id,
            event.event_type,
            event.event_id,
            "accepted" if inserted else "duplicate",
        )
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        logger.info("%s - %s", self.address_string(), fmt % args)


class WebhookServer(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, db_path: Path) -> None:
        super().__init__((host, port), WebhookHandler)
        self.db_path = db_path


def main() -> None:
    host = os.getenv("WEBHOOK_RECEIVER_HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = int(os.getenv("WEBHOOK_RECEIVER_PORT", "8790") or "8790")
    db_path = db_path_from_env()
    init_db(db_path)
    server = WebhookServer(host, port, db_path)
    logger.info("Webhook receiver listening on %s:%s db=%s", host, port, db_path)
    server.serve_forever()


if __name__ == "__main__":
    main()
