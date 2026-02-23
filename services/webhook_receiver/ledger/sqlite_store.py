from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .interface import AsyncJobInsert, EventStore, RunEventInsert, WebhookEventInsert


class SQLiteEventStore(EventStore):
    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    def insert_webhook_event_if_absent(self, event: WebhookEventInsert) -> bool:
        with self._lock:
            with self._conn() as conn:
                try:
                    conn.execute(
                        """
                        INSERT INTO webhook_events (
                          provider, idempotency_key, event_type, event_id, received_at_utc,
                          payload_json, headers_json, signature_valid
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event.provider,
                            event.idempotency_key,
                            event.event_type,
                            event.event_id,
                            event.received_at_utc,
                            event.payload_json,
                            event.headers_json,
                            1 if event.signature_valid else 0,
                        ),
                    )
                    conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    return False

    def append_run_event(self, event: RunEventInsert) -> None:
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO run_events (
                      run_id, phase, step_id, partition_id, provider,
                      event_type, event_id, provider_ref, webhook_event_id,
                      dedupe_key, orphaned, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                    """,
                    (
                        event.run_id,
                        event.phase,
                        event.step_id,
                        event.partition_id,
                        event.provider,
                        event.event_type,
                        event.event_id,
                        event.provider_ref,
                        event.webhook_event_id,
                        event.dedupe_key,
                        1 if event.orphaned else 0,
                    ),
                )
                conn.commit()

    def register_async_job(self, job: AsyncJobInsert) -> None:
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    """
                    INSERT INTO async_jobs (
                      provider, job_kind, external_job_id, run_id, phase,
                      step_id, partition_id, attempt, status, last_error,
                      created_at_utc, updated_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                    ON CONFLICT(provider, external_job_id, attempt)
                    DO UPDATE SET
                      status=excluded.status,
                      last_error=excluded.last_error,
                      updated_at_utc=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                    """,
                    (
                        job.provider,
                        job.job_kind,
                        job.external_job_id,
                        job.run_id,
                        job.phase,
                        job.step_id,
                        job.partition_id,
                        job.attempt,
                        job.status,
                        job.last_error,
                    ),
                )
                conn.commit()

    def list_pending_jobs(self, provider: str, run_id: Optional[str], phase: Optional[str]) -> List[Dict[str, Any]]:
        clauses = ["provider = ?", "status IN ('submitted','running')"]
        params: List[Any] = [provider]
        if run_id:
            clauses.append("run_id = ?")
            params.append(run_id)
        if phase:
            clauses.append("phase = ?")
            params.append(phase)
        where = " AND ".join(clauses)
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM async_jobs
                WHERE {where}
                ORDER BY updated_at_utc DESC, id DESC
                """,
                tuple(params),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_async_job_status(
        self,
        *,
        provider: str,
        external_job_id: str,
        attempt: int,
        status: str,
        last_error: Optional[str],
    ) -> None:
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    """
                    UPDATE async_jobs
                    SET status = ?,
                        last_error = ?,
                        updated_at_utc = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                    WHERE provider = ? AND external_job_id = ? AND attempt = ?
                    """,
                    (status, last_error, provider, external_job_id, attempt),
                )
                conn.commit()

    def latest_attempt_for_tuple(self, *, run_id: str, phase: str, step_id: str, partition_id: str) -> Optional[int]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT MAX(attempt) AS max_attempt
                FROM async_jobs
                WHERE run_id = ? AND phase = ? AND step_id = ? AND partition_id = ?
                """,
                (run_id, phase, step_id, partition_id),
            ).fetchone()
        if not row:
            return None
        value = row["max_attempt"]
        return int(value) if value is not None else None

    def find_async_job(
        self,
        *,
        provider: str,
        external_job_id: str,
        attempt: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        clauses = ["provider = ?", "external_job_id = ?"]
        params: List[Any] = [provider, external_job_id]
        if attempt is not None:
            clauses.append("attempt = ?")
            params.append(int(attempt))
            order = ""
        else:
            order = "ORDER BY attempt DESC"
        with self._conn() as conn:
            row = conn.execute(
                f"""
                SELECT * FROM async_jobs
                WHERE {' AND '.join(clauses)}
                {order}
                LIMIT 1
                """,
                tuple(params),
            ).fetchone()
        return dict(row) if row else None

    def fetch_webhook_event_id(self, provider: str, idempotency_key: str) -> Optional[int]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT id FROM webhook_events
                WHERE provider = ? AND idempotency_key = ?
                LIMIT 1
                """,
                (provider, idempotency_key),
            ).fetchone()
        if not row:
            return None
        return int(row["id"])

    def count_webhook_events(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM webhook_events").fetchone()
        return int(row["c"]) if row else 0

    def count_run_events(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM run_events").fetchone()
        return int(row["c"]) if row else 0

    def dump_recent_provider_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, provider, idempotency_key, event_id, event_type, received_at_utc
                FROM webhook_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_completed_provider_refs(self, *, provider: str, run_id: str, phase: str) -> List[str]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT provider_ref FROM run_events
                WHERE provider = ? AND run_id = ? AND phase = ?
                  AND orphaned = 0 AND provider_ref IS NOT NULL
                  AND event_type IN ('response.completed', 'batch.completed')
                """,
                (provider, run_id, phase),
            ).fetchall()
        return [str(row["provider_ref"]) for row in rows if row["provider_ref"]]

    def fetch_webhook_payload(self, *, provider: str, run_id: str, provider_ref: str) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT w.payload_json
                FROM run_events r
                JOIN webhook_events w ON r.webhook_event_id = w.id
                WHERE r.provider = ? AND r.run_id = ? AND r.provider_ref = ?
                  AND r.orphaned = 0 AND r.webhook_event_id IS NOT NULL
                ORDER BY r.id DESC
                LIMIT 1
                """,
                (provider, run_id, provider_ref),
            ).fetchone()
        return str(row["payload_json"]) if row else None

    def dump_recent_run_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, run_id, phase, step_id, partition_id, provider, event_type,
                       event_id, provider_ref, webhook_event_id, dedupe_key, orphaned, created_at_utc
                FROM run_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]
