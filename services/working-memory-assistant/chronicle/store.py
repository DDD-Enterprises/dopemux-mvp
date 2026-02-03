"""
Chronicle Store - SQLite canonical storage for Dope-Memory.

Handles:
- Raw activity events (short retention)
- Curated work log entries (durable)
- Issue links
- Schema initialization and migrations
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class ChronicleStore:
    """SQLite canonical store for Dope-Memory chronicle data."""

    def __init__(self, db_path: str | Path):
        """Initialize the chronicle store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def initialize_schema(self) -> None:
        """Initialize database schema from SQL file."""
        conn = self.connect()
        schema_sql = SCHEMA_PATH.read_text()
        conn.executescript(schema_sql)
        conn.commit()

    # ─────────────────────────────────────────────────────────────────
    # Raw Activity Events
    # ─────────────────────────────────────────────────────────────────

    def insert_raw_event(
        self,
        workspace_id: str,
        instance_id: str,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        *,
        event_id: Optional[str] = None,
        ts_utc: Optional[str] = None,
        session_id: Optional[str] = None,
        redaction_level: str = "strict",
        ttl_days: int = 7,
    ) -> str:
        """Insert a raw activity event.

        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            event_type: Type of event
            source: Source service/component
            payload: Event payload (already redacted)
            event_id: Optional event ID (auto-generated if not provided)
            ts_utc: Optional timestamp (uses current time if not provided)
            session_id: Optional session identifier
            redaction_level: Level of redaction applied
            ttl_days: Days before automatic cleanup

        Returns:
            The event ID (generated or provided)
        """
        final_event_id = event_id or str(uuid.uuid4())
        now_utc = ts_utc or datetime.now(timezone.utc).isoformat()

        conn = self.connect()
        conn.execute(
            """
            INSERT INTO raw_activity_events (
                id, workspace_id, instance_id, session_id,
                ts_utc, event_type, source,
                payload_json, redaction_level, ttl_days, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                final_event_id,
                workspace_id,
                instance_id,
                session_id,
                now_utc,
                event_type,
                source,
                json.dumps(payload),
                redaction_level,
                ttl_days,
                datetime.now(timezone.utc).isoformat(),  # Always use current time for created_at
            ),
        )
        conn.commit()
        return final_event_id


    def cleanup_expired_raw_events(self) -> int:
        """Delete raw events past their TTL.

        Returns:
            Number of deleted rows
        """
        conn = self.connect()
        cursor = conn.execute(
            """
            DELETE FROM raw_activity_events
            WHERE datetime(ts_utc) < datetime('now', '-' || ttl_days || ' days')
            """
        )
        conn.commit()
        return cursor.rowcount

    # ─────────────────────────────────────────────────────────────────
    # Work Log Entries
    # ─────────────────────────────────────────────────────────────────

    def insert_work_log_entry(
        self,
        workspace_id: str,
        instance_id: str,
        category: str,
        entry_type: str,
        summary: str,
        *,
        session_id: Optional[str] = None,
        workflow_phase: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        outcome: str = "in_progress",
        importance_score: int = 5,
        tags: Optional[list[str]] = None,
        linked_decisions: Optional[list[str]] = None,
        linked_files: Optional[list[dict[str, str]]] = None,
        linked_commits: Optional[list[str]] = None,
        linked_chat_range: Optional[dict[str, Any]] = None,
        parent_entry_id: Optional[str] = None,
        duration_sec: Optional[int] = None,
    ) -> str:
        """Insert a curated work log entry.

        Returns:
            The generated entry ID
        """
        entry_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        conn = self.connect()
        conn.execute(
            """
            INSERT INTO work_log_entries (
                id, workspace_id, instance_id, session_id,
                ts_utc, duration_sec,
                category, entry_type, workflow_phase,
                summary, details_json, reasoning,
                outcome, importance_score, tags_json,
                linked_decisions_json, linked_files_json,
                linked_commits_json, linked_chat_range_json,
                parent_entry_id, created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                workspace_id,
                instance_id,
                session_id,
                now_utc,
                duration_sec,
                category,
                entry_type,
                workflow_phase,
                summary,
                json.dumps(details) if details else None,
                reasoning,
                outcome,
                importance_score,
                json.dumps(tags or []),
                json.dumps(linked_decisions) if linked_decisions else None,
                json.dumps(linked_files) if linked_files else None,
                json.dumps(linked_commits) if linked_commits else None,
                json.dumps(linked_chat_range) if linked_chat_range else None,
                parent_entry_id,
                now_utc,
                now_utc,
            ),
        )
        conn.commit()
        return entry_id

    def search_work_log(
        self,
        workspace_id: str,
        instance_id: str,
        *,
        query: Optional[str] = None,
        session_id: Optional[str] = None,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        workflow_phase: Optional[str] = None,
        tags_any: Optional[list[str]] = None,
        time_range: Optional[str] = None,
        limit: int = 3,
        cursor: Optional[tuple[int, str, str]] = None,
    ) -> list[dict[str, Any]]:
        """Search work log entries with deterministic ordering.

        Args:
            workspace_id: Required workspace filter
            instance_id: Required instance filter
            query: Optional keyword search (LIKE on summary)
            session_id: Optional session filter
            category: Optional category filter
            entry_type: Optional entry_type filter
            workflow_phase: Optional workflow_phase filter
            tags_any: Optional tag overlap filter
            time_range: 'today', 'week', 'month', or 'all'
            limit: Max results (default 3, ADHD boundary)
            cursor: Pagination cursor (importance_score, ts_utc, id)

        Returns:
            List of matching entries ordered by (importance_score DESC, ts_utc DESC, id ASC)
        """
        conn = self.connect()

        conditions = ["workspace_id = ?", "instance_id = ?"]
        params: list[Any] = [workspace_id, instance_id]

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if category:
            conditions.append("category = ?")
            params.append(category)

        if entry_type:
            conditions.append("entry_type = ?")
            params.append(entry_type)

        if workflow_phase:
            conditions.append("workflow_phase = ?")
            params.append(workflow_phase)

        if query:
            conditions.append("summary LIKE ?")
            params.append(f"%{query}%")

        if tags_any:
            # JSON array overlap check
            tag_conditions = []
            for tag in tags_any:
                tag_conditions.append("tags_json LIKE ?")
                params.append(f'%"{tag}"%')
            conditions.append(f"({' OR '.join(tag_conditions)})")

        if time_range and time_range != "all":
            now = datetime.now(timezone.utc)
            if time_range == "today":
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "week":
                cutoff = now - timedelta(days=7)
            elif time_range == "month":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = None

            if cutoff:
                conditions.append("ts_utc >= ?")
                params.append(cutoff.isoformat())

        # Cursor-based pagination
        if cursor:
            last_score, last_ts, last_id = cursor
            conditions.append(
                """
                (importance_score < ? OR
                 (importance_score = ? AND ts_utc < ?) OR
                 (importance_score = ? AND ts_utc = ? AND id > ?))
                """
            )
            params.extend([last_score, last_score, last_ts, last_score, last_ts, last_id])

        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT * FROM work_log_entries
            WHERE {where_clause}
            ORDER BY importance_score DESC, ts_utc DESC, id ASC
            LIMIT ?
        """
        params.append(limit)

        cursor_result = conn.execute(sql, params)
        rows = cursor_result.fetchall()

        return [dict(row) for row in rows]

    def count_work_log(
        self,
        workspace_id: str,
        instance_id: str,
        **filters: Any,
    ) -> int:
        """Count matching work log entries for more_count calculation."""
        # Reuse search logic but just count
        conn = self.connect()

        conditions = ["workspace_id = ?", "instance_id = ?"]
        params: list[Any] = [workspace_id, instance_id]

        for key in ["session_id", "category", "entry_type", "workflow_phase"]:
            if filters.get(key):
                conditions.append(f"{key} = ?")
                params.append(filters[key])

        if filters.get("query"):
            conditions.append("summary LIKE ?")
            params.append(f"%{filters['query']}%")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT COUNT(*) FROM work_log_entries WHERE {where_clause}"

        result = conn.execute(sql, params).fetchone()
        return result[0] if result else 0

    def get_entry_by_id(
        self, workspace_id: str, instance_id: str, entry_id: str
    ) -> Optional[dict[str, Any]]:
        """Get a single work log entry by ID."""
        conn = self.connect()
        result = conn.execute(
            """
            SELECT * FROM work_log_entries
            WHERE id = ? AND workspace_id = ? AND instance_id = ?
            """,
            (entry_id, workspace_id, instance_id),
        ).fetchone()
        return dict(result) if result else None

    # ─────────────────────────────────────────────────────────────────
    # Issue Links
    # ─────────────────────────────────────────────────────────────────

    def insert_issue_link(
        self,
        workspace_id: str,
        instance_id: str,
        issue_entry_id: str,
        resolution_entry_id: str,
        *,
        confidence: float = 0.7,
        evidence_window_min: int = 30,
    ) -> str:
        """Link an issue entry to its resolution."""
        link_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        conn = self.connect()
        conn.execute(
            """
            INSERT INTO issue_links (
                id, workspace_id, instance_id,
                issue_entry_id, resolution_entry_id,
                confidence, evidence_window_min, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link_id,
                workspace_id,
                instance_id,
                issue_entry_id,
                resolution_entry_id,
                confidence,
                evidence_window_min,
                now_utc,
            ),
        )
        conn.commit()
        return link_id

    # ─────────────────────────────────────────────────────────────────
    # Phase 2: Reflection Cards
    # ─────────────────────────────────────────────────────────────────

    def insert_reflection_card(self, card: dict[str, Any]) -> str:
        """Insert a reflection card.

        Args:
            card: Reflection card dict with all required fields

        Returns:
            The reflection_id
        """
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO reflection_cards (
                id, workspace_id, instance_id, session_id,
                ts_utc, window_start_utc, window_end_utc,
                trajectory, top_decisions_json, top_blockers_json,
                progress_json, next_suggested_json,
                promotion_candidates_json, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card["reflection_id"],
                card["workspace_id"],
                card["instance_id"],
                card.get("session_id"),
                datetime.now(timezone.utc).isoformat(),
                card["window_start"],
                card["window_end"],
                card["trajectory_summary"],
                json.dumps(card["top_decisions"]),
                json.dumps(card["top_blockers"]),
                json.dumps(card["progress_summary"]),
                json.dumps(card["suggested_next"]),
                json.dumps(card.get("promotion_candidates", [])),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return card["reflection_id"]

    def get_reflection_cards(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Get recent reflection cards.

        Args:
            workspace_id: Workspace filter
            instance_id: Instance filter
            session_id: Optional session filter
            limit: Max results (default 3)

        Returns:
            List of reflection card dicts
        """
        conn = self.connect()

        if session_id:
            rows = conn.execute(
                """
                SELECT id, ts_utc, trajectory, top_decisions_json,
                       top_blockers_json, progress_json, next_suggested_json
                FROM reflection_cards
                WHERE workspace_id = ? AND instance_id = ? AND session_id = ?
                ORDER BY ts_utc DESC
                LIMIT ?
                """,
                (workspace_id, instance_id, session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, ts_utc, trajectory, top_decisions_json,
                       top_blockers_json, progress_json, next_suggested_json
                FROM reflection_cards
                WHERE workspace_id = ? AND instance_id = ?
                ORDER BY ts_utc DESC
                LIMIT ?
                """,
                (workspace_id, instance_id, limit),
            ).fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "ts_utc": row["ts_utc"],
                "trajectory": row["trajectory"],
                "top_decisions": json.loads(row["top_decisions_json"]),
                "top_blockers": json.loads(row["top_blockers_json"]),
                "progress": json.loads(row["progress_json"]),
                "next_suggested": json.loads(row["next_suggested_json"]),
            })

        return results

    # ─────────────────────────────────────────────────────────────────
    # Phase 2: Trajectory State
    # ─────────────────────────────────────────────────────────────────

    def upsert_trajectory_state(
        self, workspace_id: str, instance_id: str, state: dict[str, Any]
    ) -> None:
        """Insert or update trajectory state.

        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            state: Trajectory state dict
        """
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO trajectory_state (
                workspace_id, instance_id, session_id,
                updated_at_utc, current_stream, current_goal_json, last_steps_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(workspace_id, instance_id) DO UPDATE SET
                session_id = excluded.session_id,
                updated_at_utc = excluded.updated_at_utc,
                current_stream = excluded.current_stream,
                current_goal_json = excluded.current_goal_json,
                last_steps_json = excluded.last_steps_json
            """,
            (
                workspace_id,
                instance_id,
                state.get("session_id"),
                state["updated_at_utc"],
                state.get("current_stream", ""),
                json.dumps(state.get("current_goal", {})),
                json.dumps(state.get("last_steps", [])),
            ),
        )
        conn.commit()

    def get_trajectory_state(
        self, workspace_id: str, instance_id: str
    ) -> Optional[dict[str, Any]]:
        """Get current trajectory state.

        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier

        Returns:
            Trajectory state dict or None
        """
        conn = self.connect()
        row = conn.execute(
            """
            SELECT session_id, updated_at_utc, current_stream,
                   current_goal_json, last_steps_json
            FROM trajectory_state
            WHERE workspace_id = ? AND instance_id = ?
            """,
            (workspace_id, instance_id),
        ).fetchone()

        if not row:
            return None

        return {
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "session_id": row["session_id"],
            "updated_at_utc": row["updated_at_utc"],
            "current_stream": row["current_stream"],
            "current_goal": json.loads(row["current_goal_json"]),
            "last_steps": json.loads(row["last_steps_json"]),
        }

    # ─────────────────────────────────────────────────────────────────
    # Phase 2: Helper Queries
    # ─────────────────────────────────────────────────────────────────

    def get_work_log_window(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str],
        window_start: str,
        window_end: str,
    ) -> list[dict[str, Any]]:
        """Get work log entries in a time window.

        Args:
            workspace_id: Workspace filter
            instance_id: Instance filter
            session_id: Optional session filter
            window_start: ISO timestamp
            window_end: ISO timestamp

        Returns:
            List of work log entry dicts
        """
        conn = self.connect()

        if session_id:
            rows = conn.execute(
                """
                SELECT * FROM work_log_entries
                WHERE workspace_id = ? AND instance_id = ? AND session_id = ?
                  AND ts_utc >= ? AND ts_utc <= ?
                ORDER BY importance_score DESC, ts_utc DESC, id ASC
                """,
                (workspace_id, instance_id, session_id, window_start, window_end),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM work_log_entries
                WHERE workspace_id = ? AND instance_id = ?
                  AND ts_utc >= ? AND ts_utc <= ?
                ORDER BY importance_score DESC, ts_utc DESC, id ASC
                """,
                (workspace_id, instance_id, window_start, window_end),
            ).fetchall()

        return [dict(row) for row in rows]
