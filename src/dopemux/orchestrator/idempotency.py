import os
import sqlite3
import time
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class IdempotencyState(Enum):
    INTENT = "intent_to_transition"
    TRANSITIONING = "transitioning"
    COMPLETED = "completed"


class IdempotencyStore:
    """SQLite-backed persistent store for workflow transitions."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            xdg_share = os.path.expanduser("~/.local/share/dopemux")
            os.makedirs(xdg_share, exist_ok=True)
            self.db_path = os.path.join(xdg_share, "idempotency.db")
        
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        # Enforce explicit transaction control with isolation_level=None
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        
        # Enforce WAL mode and busy timeout for concurrent safety
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS idempotency_records (
                        idempotency_key TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        workflow_id TEXT NOT NULL,
                        transition_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        response_json TEXT
                    );
                """)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(idempotency_records);")
                columns = [row[1] for row in cursor.fetchall()]
                if "response_json" not in columns:
                    conn.execute("ALTER TABLE idempotency_records ADD COLUMN response_json TEXT;")
                conn.execute("COMMIT;")
            except Exception as e:
                conn.execute("ROLLBACK;")
                raise e

    def claim_transition(
        self,
        idempotency_key: str,
        project_id: str,
        workflow_id: str,
        transition_name: str,
        max_wait_seconds: float = 2.0,
        poll_interval: float = 0.05,
        lease_timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Atomically claim the transition lock using a BEGIN IMMEDIATE transaction.
        
        If another thread is already transitioning, this method blocks and polls the database
        until either:
        1. The transition completes (and returns the cached result).
        2. The transition rolls back to INTENT (in which case we claim it and proceed).
        3. The transition lease expires (stale worker, in which case we hijack it and proceed).
        4. The max wait time is exceeded, raising a RuntimeError.
        
        Returns:
            A dict with:
                "action": "PROCEED" | "COMPLETED"
                "response_json": Optional[str]
        
        Raises:
            RuntimeError: If transition is in progress and we timeout waiting.
        """
        start_time = time.time()
        while True:
            conn = self._get_connection()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status, response_json, updated_at, project_id, workflow_id, transition_name FROM idempotency_records WHERE idempotency_key = ?;",
                    (idempotency_key,)
                )
                row = cursor.fetchone()
                
                now = datetime.now(timezone.utc).isoformat()
                
                if row is None:
                    # Case A: No record exists. Atomic insert as TRANSITIONING.
                    conn.execute(
                        """
                        INSERT INTO idempotency_records 
                        (idempotency_key, project_id, workflow_id, transition_name, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            idempotency_key,
                            project_id,
                            workflow_id,
                            transition_name,
                            IdempotencyState.TRANSITIONING.value,
                            now,
                            now
                        )
                    )
                    conn.execute("COMMIT;")
                    return {"action": "PROCEED", "response_json": None}
                
                # Reject reused idempotency keys for different transitions
                if (
                    row["project_id"] != project_id or 
                    row["workflow_id"] != workflow_id or 
                    row["transition_name"] != transition_name
                ):
                    conn.execute("COMMIT;")
                    raise ValueError(
                        f"Idempotency key '{idempotency_key}' is already used for a different transition: "
                        f"{row['project_id']}/{row['workflow_id']}/{row['transition_name']} "
                        f"(requested: {project_id}/{workflow_id}/{transition_name})"
                    )

                status = row["status"]
                response_json = row["response_json"]
                updated_at_str = row["updated_at"]
                
                # Check for lease expiration
                is_expired = False
                try:
                    updated_at = datetime.fromisoformat(updated_at_str)
                    elapsed = (datetime.now(timezone.utc) - updated_at).total_seconds()
                    if elapsed > lease_timeout_seconds:
                        is_expired = True
                except Exception:
                    pass  # If date parsing fails, do not assume expired
                
                if status == IdempotencyState.COMPLETED.value:
                    # Case B: Completed transition. Return cached result.
                    conn.execute("COMMIT;")
                    return {"action": "COMPLETED", "response_json": response_json}
                
                elif status == IdempotencyState.INTENT.value or (status == IdempotencyState.TRANSITIONING.value and is_expired):
                    # Case C: Exists as INTENT or lease expired. Atomically update status to TRANSITIONING.
                    conn.execute(
                        """
                        UPDATE idempotency_records
                        SET status = ?, updated_at = ?
                        WHERE idempotency_key = ?;
                        """,
                        (IdempotencyState.TRANSITIONING.value, now, idempotency_key)
                    )
                    conn.execute("COMMIT;")
                    return {"action": "PROCEED", "response_json": None}
                
                elif status == IdempotencyState.TRANSITIONING.value:
                    # Case D: Active transitioning. Release lock immediately to avoid blocking others, then wait.
                    conn.execute("COMMIT;")
            except Exception as e:
                try:
                    conn.execute("ROLLBACK;")
                except Exception:
                    pass
                raise e
            finally:
                conn.close()
            
            # Check for wait timeout
            if time.time() - start_time >= max_wait_seconds:
                raise RuntimeError("Transition already in progress")
            
            time.sleep(poll_interval)

    def record_intent(
        self,
        idempotency_key: str,
        project_id: str,
        workflow_id: str,
        transition_name: str
    ):
        """Phase 1: Record intent to transition workflow state."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute(
                    """
                    INSERT INTO idempotency_records 
                    (idempotency_key, project_id, workflow_id, transition_name, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(idempotency_key) DO UPDATE SET
                        project_id=excluded.project_id,
                        workflow_id=excluded.workflow_id,
                        transition_name=excluded.transition_name,
                        updated_at=excluded.updated_at;
                    """,
                    (
                        idempotency_key,
                        project_id,
                        workflow_id,
                        transition_name,
                        IdempotencyState.INTENT.value,
                        now,
                        now
                    )
                )
                conn.execute("COMMIT;")
            except Exception as e:
                conn.execute("ROLLBACK;")
                raise e

    def update_status(self, idempotency_key: str, status: IdempotencyState, response_json: Optional[str] = None):
        """Phase 2 & 3: Update transition status (transitioning or completed)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                if response_json is not None:
                    conn.execute(
                        """
                        UPDATE idempotency_records
                        SET status = ?, updated_at = ?, response_json = ?
                        WHERE idempotency_key = ?;
                        """,
                        (status.value, now, response_json, idempotency_key)
                    )
                else:
                    conn.execute(
                        """
                        UPDATE idempotency_records
                        SET status = ?, updated_at = ?
                        WHERE idempotency_key = ?;
                        """,
                        (status.value, now, idempotency_key)
                    )
                conn.execute("COMMIT;")
            except Exception as e:
                conn.execute("ROLLBACK;")
                raise e

    def get_record(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve idempotency record by key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM idempotency_records WHERE idempotency_key = ?;",
                (idempotency_key,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_incomplete_records(self) -> List[Dict[str, Any]]:
        """Retrieve all incomplete records (intent_to_transition or transitioning)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM idempotency_records 
                WHERE status IN (?, ?);
                """,
                (IdempotencyState.INTENT.value, IdempotencyState.TRANSITIONING.value)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
