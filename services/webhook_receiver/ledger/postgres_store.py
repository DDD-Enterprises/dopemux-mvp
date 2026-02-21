from __future__ import annotations

from typing import Any, Dict, List, Optional

from .interface import AsyncJobInsert, EventStore, RunEventInsert, WebhookEventInsert


class PostgresEventStore(EventStore):
    def __init__(self, db_url: str) -> None:
        self._db_url = db_url

    def _connect(self):
        try:
            import psycopg2
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("psycopg2 is required for postgres WEBHOOK_DB_URL") from exc
        return psycopg2.connect(self._db_url)

    def _dict_row_factory(self):
        import psycopg2.extras

        return psycopg2.extras.RealDictCursor

    def insert_webhook_event_if_absent(self, event: WebhookEventInsert) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO webhook_events (
                      provider, idempotency_key, event_type, event_id, received_at_utc,
                      payload_json, headers_json, signature_valid
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    ON CONFLICT (provider, idempotency_key) DO NOTHING
                    """,
                    (
                        event.provider,
                        event.idempotency_key,
                        event.event_type,
                        event.event_id,
                        event.received_at_utc,
                        event.payload_json,
                        event.headers_json,
                        bool(event.signature_valid),
                    ),
                )
                return int(cur.rowcount or 0) > 0

    def append_run_event(self, event: RunEventInsert) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO run_events (
                      run_id, phase, step_id, partition_id, provider,
                      event_type, event_id, provider_ref, webhook_event_id,
                      dedupe_key, orphaned, created_at_utc
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now() at time zone 'utc')
                    ON CONFLICT (dedupe_key) DO NOTHING
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
                        bool(event.orphaned),
                    ),
                )

    def register_async_job(self, job: AsyncJobInsert) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO async_jobs (
                      provider, job_kind, external_job_id, run_id, phase,
                      step_id, partition_id, attempt, status, last_error,
                      created_at_utc, updated_at_utc
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now() at time zone 'utc', now() at time zone 'utc')
                    ON CONFLICT(provider, external_job_id, attempt)
                    DO UPDATE SET
                      status=EXCLUDED.status,
                      last_error=EXCLUDED.last_error,
                      updated_at_utc=now() at time zone 'utc'
                    """,
                    (
                        job.provider,
                        job.job_kind,
                        job.external_job_id,
                        job.run_id,
                        job.phase,
                        job.step_id,
                        job.partition_id,
                        int(job.attempt),
                        job.status,
                        job.last_error,
                    ),
                )

    def list_pending_jobs(self, provider: str, run_id: Optional[str], phase: Optional[str]) -> List[Dict[str, Any]]:
        clauses = ["provider = %s", "status IN ('submitted','running')"]
        params: List[Any] = [provider]
        if run_id:
            clauses.append("run_id = %s")
            params.append(run_id)
        if phase:
            clauses.append("phase = %s")
            params.append(phase)
        with self._connect() as conn:
            with conn.cursor(cursor_factory=self._dict_row_factory()) as cur:
                cur.execute(
                    f"""
                    SELECT *
                    FROM async_jobs
                    WHERE {' AND '.join(clauses)}
                    ORDER BY updated_at_utc DESC, id DESC
                    """,
                    tuple(params),
                )
                return list(cur.fetchall())

    def update_async_job_status(
        self,
        *,
        provider: str,
        external_job_id: str,
        attempt: int,
        status: str,
        last_error: Optional[str],
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE async_jobs
                    SET status = %s,
                        last_error = %s,
                        updated_at_utc = now() at time zone 'utc'
                    WHERE provider = %s AND external_job_id = %s AND attempt = %s
                    """,
                    (status, last_error, provider, external_job_id, int(attempt)),
                )

    def latest_attempt_for_tuple(self, *, run_id: str, phase: str, step_id: str, partition_id: str) -> Optional[int]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT MAX(attempt)
                    FROM async_jobs
                    WHERE run_id = %s AND phase = %s AND step_id = %s AND partition_id = %s
                    """,
                    (run_id, phase, step_id, partition_id),
                )
                row = cur.fetchone()
                if not row or row[0] is None:
                    return None
                return int(row[0])

    def find_async_job(
        self,
        *,
        provider: str,
        external_job_id: str,
        attempt: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        clauses = ["provider = %s", "external_job_id = %s"]
        params: List[Any] = [provider, external_job_id]
        if attempt is not None:
            clauses.append("attempt = %s")
            params.append(int(attempt))
        order_clause = "ORDER BY attempt DESC"
        with self._connect() as conn:
            with conn.cursor(row_factory=self._dict_row_factory()) as cur:
                cur.execute(
                    f"""
                    SELECT *
                    FROM async_jobs
                    WHERE {' AND '.join(clauses)}
                    {order_clause}
                    LIMIT 1
                    """,
                    tuple(params),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def fetch_webhook_event_id(self, provider: str, idempotency_key: str) -> Optional[int]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM webhook_events
                    WHERE provider = %s AND idempotency_key = %s
                    LIMIT 1
                    """,
                    (provider, idempotency_key),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return int(row[0])

    def count_webhook_events(self) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM webhook_events")
                row = cur.fetchone()
                return int(row[0]) if row else 0

    def count_run_events(self) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM run_events")
                row = cur.fetchone()
                return int(row[0]) if row else 0

    def list_completed_provider_refs(self, *, provider: str, run_id: str, phase: str) -> List[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT provider_ref FROM run_events
                    WHERE provider = %s AND run_id = %s AND phase = %s
                      AND orphaned = FALSE AND provider_ref IS NOT NULL
                      AND event_type IN ('response.completed', 'batch.completed')
                    """,
                    (provider, run_id, phase),
                )
                return [str(row[0]) for row in cur.fetchall() if row[0]]

    def fetch_webhook_payload(self, *, provider: str, run_id: str, provider_ref: str) -> Optional[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT w.payload_json
                    FROM run_events r
                    JOIN webhook_events w ON r.webhook_event_id = w.id
                    WHERE r.provider = %s AND r.run_id = %s AND r.provider_ref = %s
                      AND r.orphaned = FALSE AND r.webhook_event_id IS NOT NULL
                    ORDER BY r.id DESC
                    LIMIT 1
                    """,
                    (provider, run_id, provider_ref),
                )
                row = cur.fetchone()
                if not row or row[0] is None:
                    return None
                import json
                return json.dumps(row[0]) if isinstance(row[0], dict) else str(row[0])
