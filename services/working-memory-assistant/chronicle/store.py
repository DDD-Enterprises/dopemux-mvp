"""
Chronicle Store - SQLite canonical storage for Dope-Memory.

Handles:
- Raw activity events (short retention)
- Curated work log entries (durable)
- Issue links
- Schema initialization and migrations
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from ulid import ULID
    def _generate_ulid() -> str:
        return str(ULID())
except ImportError:
    import time as _time
    import os as _os
    import base64 as _base64
    def _generate_ulid() -> str:
        """Fallback ULID-like generator when ulid-py not installed."""
        ts = int(_time.time() * 1000).to_bytes(6, 'big')
        rand = _os.urandom(10)
        return (ts + rand).hex()

MAX_CHAIN_DEPTH = 10

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
    # Supersession Helpers (Packet F)
    # ─────────────────────────────────────────────────────────────────

    def _get_superseded_entry_ids(self) -> set[str]:
        """Return set of entry IDs that have been superseded.
        
        An entry is superseded if its ID appears as supersedes_entry_id
        in another entry.
        """
        conn = self.connect()
        rows = conn.execute(
            "SELECT supersedes_entry_id FROM work_log_entries WHERE supersedes_entry_id IS NOT NULL"
        ).fetchall()
        return {row[0] for row in rows}

    def _get_chain_depth(self, entry_id: str) -> int:
        """Count the number of entries in the supersession chain ending at entry_id.
        
        Traverses backward (from newest to oldest) via supersedes_entry_id.
        Uses a visited set for cycle detection.
        Returns 1 for an entry with no predecessor.
        """
        conn = self.connect()
        depth = 1
        current_id = entry_id
        visited: set[str] = {current_id}
        
        while True:
            row = conn.execute(
                "SELECT supersedes_entry_id FROM work_log_entries WHERE id = ?",
                (current_id,),
            ).fetchone()
            if not row or row[0] is None:
                break
            predecessor_id = row[0]
            if predecessor_id in visited:
                raise ValueError(
                    f"Cycle detected in supersession chain at entry {predecessor_id}"
                )
            visited.add(predecessor_id)
            depth += 1
            current_id = predecessor_id
        
        return depth

    def _resolve_chain_head(self, entry_id: str) -> str:
        """Given any entry ID, walk forward to find the current chain head.
        
        The head is the entry that is not itself superseded by any other entry.
        """
        conn = self.connect()
        current_id = entry_id
        visited: set[str] = {current_id}
        
        while True:
            row = conn.execute(
                "SELECT id FROM work_log_entries WHERE supersedes_entry_id = ?",
                (current_id,),
            ).fetchone()
            if not row:
                return current_id
            successor_id = row[0]
            if successor_id in visited:
                raise ValueError(
                    f"Cycle detected in supersession chain at entry {successor_id}"
                )
            visited.add(successor_id)
            current_id = successor_id

    def _is_entry_superseded(self, entry_id: str) -> bool:
        """Check if an entry has been superseded by another entry."""
        conn = self.connect()
        row = conn.execute(
            "SELECT COUNT(*) FROM work_log_entries WHERE supersedes_entry_id = ?",
            (entry_id,),
        ).fetchone()
        return row[0] > 0

    def _compute_chain_annotations(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Add supersession chain annotations to a list of entries.
        
        Annotations (computed at read time, never stored):
        - superseded_by: entry_id of the superseding entry (if superseded)
        - supersedes: entry_id of the entry this one supersedes
        - chain_position: {position: N, depth: M} (1-indexed from origin)
        - is_head: true if this is the current active version
        """
        if not entries:
            return entries
        
        conn = self.connect()
        superseded_ids = self._get_superseded_entry_ids()
        
        # Build lookup: superseded_id -> superseding_id
        superseding_map: dict[str, str] = {}
        rows = conn.execute(
            "SELECT id, supersedes_entry_id FROM work_log_entries WHERE supersedes_entry_id IS NOT NULL"
        ).fetchall()
        for row in rows:
            superseding_map[row[1]] = row[0]
        
        annotated = []
        for entry in entries:
            eid = entry["id"]
            supersedes = entry.get("supersedes_entry_id")
            is_head = eid not in superseded_ids
            superseded_by = superseding_map.get(eid)
            
            # Compute chain position and depth
            chain_position = None
            if supersedes or superseded_by:
                # Walk backward to origin to find position
                position = 1
                current = eid
                while True:
                    row_data = conn.execute(
                        "SELECT supersedes_entry_id FROM work_log_entries WHERE id = ?",
                        (current,),
                    ).fetchone()
                    if not row_data or row_data[0] is None:
                        break
                    position += 1
                    current = row_data[0]
                
                # Walk forward from origin to find total depth
                head = self._resolve_chain_head(eid)
                depth = self._get_chain_depth(head)
                chain_position = {"position": depth - position + 1, "depth": depth}
            
            annotated_entry = {
                **entry,
                "is_head": is_head,
                "superseded_by": superseded_by,
                "supersedes": supersedes,
                "chain_position": chain_position,
            }
            annotated.append(annotated_entry)
        
        return annotated

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
            INSERT OR IGNORE INTO raw_activity_events (
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
        # Provenance fields (Packet D §4.3 - REQUIRED, never optional)
        source_event_id: str,
        source_event_type: str,
        source_adapter: str,
        source_event_ts_utc: str,
        promotion_rule: str,
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
        supersedes_entry_id: Optional[str] = None,
        duration_sec: Optional[int] = None,
    ) -> str:
        """Insert a curated work log entry with provenance.
        
        Per Packet D §4.3: All provenance fields are REQUIRED and NOT NULL.
        Per Packet D §7.7: entry_id is deterministic (sha256 of provenance).
        Per Packet D §5.3: ts_utc is event time, not promotion time.
        Per Packet F §3.2: Supersession chains must be linear.
        Per Packet F §3.4: Maximum chain depth is 10.

        Returns:
            The generated entry ID (deterministic)
        """
        # Validate provenance fields (Packet D §4.5 - fail-closed)
        if not all([source_event_id, source_event_type, source_adapter, source_event_ts_utc, promotion_rule]):
            raise ValueError(
                f"All provenance fields are required: source_event_id={bool(source_event_id)}, "
                f"source_event_type={bool(source_event_type)}, source_adapter={bool(source_adapter)}, "
                f"source_event_ts_utc={bool(source_event_ts_utc)}, promotion_rule={bool(promotion_rule)}"
            )
        
        # Sentinel ban (Packet D §7.8)
        sentinel_values = {'pre_migration', 'unknown', ''}
        if (source_event_id in sentinel_values or source_adapter in sentinel_values or 
            promotion_rule in sentinel_values):
            raise ValueError(
                f"Sentinel values not allowed for runtime promotions: "
                f"source_event_id={source_event_id}, source_adapter={source_adapter}, "
                f"promotion_rule={promotion_rule}"
            )
        
        # Supersession chain validation (Packet F §3.2, §3.4)
        if supersedes_entry_id:
            # Verify target entry exists
            target = self.get_entry_by_id(workspace_id, instance_id, supersedes_entry_id)
            if not target:
                raise ValueError(
                    f"Cannot supersede non-existent entry: {supersedes_entry_id}"
                )
            # Verify target is the chain head (Packet F §6.5 rule)
            if self._is_entry_superseded(supersedes_entry_id):
                head = self._resolve_chain_head(supersedes_entry_id)
                raise ValueError(
                    f"Cannot supersede entry {supersedes_entry_id} — it is already superseded. "
                    f"Target the chain head instead: {head}"
                )
            # Verify chain depth limit (Packet F §3.4)
            current_depth = self._get_chain_depth(supersedes_entry_id)
            if current_depth >= MAX_CHAIN_DEPTH:
                raise ValueError(
                    f"Supersession chain depth limit exceeded (max {MAX_CHAIN_DEPTH}). "
                    f"Current chain has {current_depth} entries."
                )
        
        # Deterministic entry_id (Packet D §7.7)
        fingerprint = f"{source_event_id}|{promotion_rule}|{source_event_ts_utc}"
        entry_id = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
        
        # Timestamps (Packet D §5.2)
        ts_utc = source_event_ts_utc  # Event time (authoritative for chronology)
        promotion_ts_utc = datetime.now(timezone.utc).isoformat()  # Promotion processing time
        created_at_utc = datetime.now(timezone.utc).isoformat()  # Physical write time

        conn = self.connect()
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO work_log_entries (
                id, workspace_id, instance_id, session_id,
                ts_utc, duration_sec,
                category, entry_type, workflow_phase,
                summary, details_json, reasoning,
                outcome, importance_score, tags_json,
                linked_decisions_json, linked_files_json,
                linked_commits_json, linked_chat_range_json,
                parent_entry_id,
                source_event_id, source_event_type, source_adapter,
                source_event_ts_utc, promotion_rule, promotion_ts_utc,
                supersedes_entry_id,
                created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                workspace_id,
                instance_id,
                session_id,
                ts_utc,  # Event time, NOT wall clock (Packet D §5.3)
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
                source_event_id,
                source_event_type,
                source_adapter,
                source_event_ts_utc,
                promotion_rule,
                promotion_ts_utc,
                supersedes_entry_id,
                created_at_utc,
                created_at_utc,  # updated_at_utc = created_at_utc for immutable entries
            ),
        )
        conn.commit()

        # Loud fail for supersession conflicts (Packet F §3.2 fork prevention)
        if cursor.rowcount == 0 and supersedes_entry_id:
            # Check if it was ignored because entry_id matches (OK) 
            # or because supersedes_entry_id matches a DIFFERENT entry (FAIL)
            existing = self.get_entry_by_id(workspace_id, instance_id, entry_id)
            if not existing:
                # If entry_id doesn't exist but rowcount was 0, 
                # then it MUST be the supersedes_entry_id UNIQUE constraint.
                row = conn.execute(
                    "SELECT id FROM work_log_entries WHERE supersedes_entry_id = ?",
                    (supersedes_entry_id,),
                ).fetchone()
                if row:
                    raise ValueError(
                        f"Supersession fork attempt rejected. Entry {supersedes_entry_id} "
                        f"is already superseded by {row[0]}."
                    )

        return entry_id
    
    def insert_promoted_entry(
        self,
        workspace_id: str,
        instance_id: str,
        promoted: Any,  # PromotedEntry from promotion.promotion
        session_id: Optional[str] = None,
    ) -> str:
        """Convenience method to insert a PromotedEntry object.
        
        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            promoted: PromotedEntry dataclass instance with all fields populated
            session_id: Optional session override
            
        Returns:
            The generated entry ID (deterministic)
        """
        return self.insert_work_log_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            category=promoted.category,
            entry_type=promoted.entry_type,
            summary=promoted.summary,
            source_event_id=promoted.source_event_id,
            source_event_type=promoted.source_event_type,
            source_adapter=promoted.source_adapter,
            source_event_ts_utc=promoted.source_event_ts_utc,
            promotion_rule=promoted.promotion_rule,
            session_id=session_id,
            workflow_phase=promoted.workflow_phase,
            details=promoted.details,
            reasoning=promoted.reasoning,
            outcome=promoted.outcome,
            importance_score=promoted.importance_score,
            tags=promoted.tags,
            linked_decisions=promoted.linked_decisions,
            linked_files=promoted.linked_files,
            linked_commits=promoted.linked_commits,
            linked_chat_range=promoted.linked_chat_range,
            supersedes_entry_id=promoted.supersedes_entry_id,
            duration_sec=promoted.duration_sec,
        )
    
    def replay_work_log(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: str,
        limit: int = 50,
        cursor: Optional[tuple[str, str]] = None,  # (ts_utc, id)
        mode: str = "replay_current",
    ) -> list[dict[str, Any]]:
        """Replay work log entries chronologically (Packet D §5.4, Packet F §5.3).
        
        Ordering: source_event_ts_utc ASC, id ASC
        
        Modes (Packet F §5.3):
        - replay_current (default): Only chain heads. Corrected narrative.
        - replay_full: All entries including superseded, with chain annotations.
        """
        conn = self.connect()
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT * FROM work_log_entries
            WHERE workspace_id = ? AND instance_id = ? AND session_id = ?
        """
        params: list[Any] = [workspace_id, instance_id, session_id]
        
        # Exclude superseded entries in replay_current mode (Packet F §5.3)
        if mode != "replay_full":
            query += """ AND id NOT IN (
                SELECT supersedes_entry_id FROM work_log_entries
                WHERE supersedes_entry_id IS NOT NULL
            )"""
        
        # Cursor pagination (keyset)
        if cursor:
            last_ts, last_id = cursor
            query += " AND (source_event_ts_utc > ? OR (source_event_ts_utc = ? AND id > ?))"
            params.extend([last_ts, last_ts, last_id])
            
        query += " ORDER BY source_event_ts_utc ASC, id ASC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, tuple(params)).fetchall()
        results = [dict(row) for row in rows]
        
        # Add chain annotations in replay_full mode (Packet F §5.3)
        if mode == "replay_full":
            results = self._compute_chain_annotations(results)
        
        return results

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
        include_superseded: bool = False,
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
            include_superseded: If True, include superseded entries with
                chain annotations. Default False (Packet F §5.1).

        Returns:
            List of matching entries ordered by (importance_score DESC, ts_utc DESC, id ASC)
        """
        conn = self.connect()

        conditions = ["workspace_id = ?", "instance_id = ?"]
        params: list[Any] = [workspace_id, instance_id]

        # Exclude superseded entries by default (Packet F §5.1)
        if not include_superseded:
            conditions.append(
                """id NOT IN (
                    SELECT supersedes_entry_id FROM work_log_entries
                    WHERE supersedes_entry_id IS NOT NULL
                )"""
            )

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
        results = [dict(row) for row in rows]

        # Add chain annotations when including superseded entries (Packet F §5.2)
        if include_superseded:
            results = self._compute_chain_annotations(results)

        return results

    def count_work_log(
        self,
        workspace_id: str,
        instance_id: str,
        **filters: Any,
    ) -> int:
        """Count matching work log entries for more_count calculation.
        
        Excludes superseded entries per Packet F §5.1.
        """
        conn = self.connect()

        conditions = ["workspace_id = ?", "instance_id = ?"]
        params: list[Any] = [workspace_id, instance_id]

        # Exclude superseded entries (Packet F §7.3)
        conditions.append(
            """id NOT IN (
                SELECT supersedes_entry_id FROM work_log_entries
                WHERE supersedes_entry_id IS NOT NULL
            )"""
        )

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
                promotion_candidates_json, created_at_utc,
                source_entry_ids_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(card.get("source_entry_ids", [])),
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
        """Get recent reflection cards with staleness detection (Packet F §7.1).

        Args:
            workspace_id: Workspace filter
            instance_id: Instance filter
            session_id: Optional session filter
            limit: Max results (default 3)

        Returns:
            List of reflection card dicts. Each card includes:
            - stale_entries: list of source entry IDs that have been superseded
            - regeneration_recommended: True if any source entries are stale
        """
        conn = self.connect()

        if session_id:
            rows = conn.execute(
                """
                SELECT id, ts_utc, window_start_utc, window_end_utc, trajectory, 
                       top_decisions_json, top_blockers_json, progress_json, next_suggested_json,
                       source_entry_ids_json
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
                SELECT id, ts_utc, window_start_utc, window_end_utc, trajectory, 
                       top_decisions_json, top_blockers_json, progress_json, next_suggested_json,
                       source_entry_ids_json
                FROM reflection_cards
                WHERE workspace_id = ? AND instance_id = ?
                ORDER BY ts_utc DESC
                LIMIT ?
                """,
                (workspace_id, instance_id, limit),
            ).fetchall()

        # Get superseded entry IDs for staleness detection (Packet F §7.1)
        superseded_ids = self._get_superseded_entry_ids()

        results = []
        for row in rows:
            source_entry_ids = json.loads(row[9]) if len(row) > 9 and row[9] else []
            stale_entries = [eid for eid in source_entry_ids if eid in superseded_ids]

            results.append(
                {
                    "reflection_id": row[0],
                    "ts_utc": row[1],
                    "window_start": row[2],
                    "window_end": row[3],
                    "trajectory_summary": row[4],
                    "top_decisions": json.loads(row[5]),
                    "top_blockers": json.loads(row[6]),
                    "progress_summary": json.loads(row[7]),
                    "suggested_next": json.loads(row[8]),
                    "source_entry_ids": source_entry_ids,
                    "stale_entries": stale_entries,
                    "regeneration_recommended": len(stale_entries) > 0,
                }
            )

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
                ORDER BY ts_utc ASC, id ASC
                """,
                (workspace_id, instance_id, session_id, window_start, window_end),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM work_log_entries
                WHERE workspace_id = ? AND instance_id = ?
                  AND ts_utc >= ? AND ts_utc <= ?
                ORDER BY ts_utc ASC, id ASC
                """,
                (workspace_id, instance_id, window_start, window_end),
            ).fetchall()

        return [dict(row) for row in rows]

    # ─────────────────────────────────────────────────────────────────
    # Packet F: Manual Correction Workflow
    # ─────────────────────────────────────────────────────────────────

    def correct_entry(
        self,
        workspace_id: str,
        instance_id: str,
        entry_id: str,
        correction_type: str,
        *,
        corrected_summary: Optional[str] = None,
        corrected_tags: Optional[list[str]] = None,
        corrected_category: Optional[str] = None,
        corrected_entry_type: Optional[str] = None,
        corrected_outcome: Optional[str] = None,
    ) -> str:
        """Create a correction entry that supersedes an existing entry.
        
        Per Packet F §6.2-§6.5:
        - Uses manual:<ULID> provenance convention
        - Validates correction_type against closed taxonomy
        - Copies all fields from original except corrected ones
        - Sets supersedes_entry_id to the original
        
        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            entry_id: ID of the entry to supersede (must be chain head)
            correction_type: One of: summary, tags, category, outcome, retraction
            corrected_*: New values for the corrected fields
            
        Returns:
            The new correcting entry's ID
        """
        # Validate correction type (Packet F §6.3 - closed taxonomy)
        valid_types = {'summary', 'tags', 'category', 'outcome', 'retraction'}
        if correction_type not in valid_types:
            raise ValueError(
                f"Invalid correction_type '{correction_type}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )
        
        # Look up the original entry
        original = self.get_entry_by_id(workspace_id, instance_id, entry_id)
        if not original:
            raise ValueError(f"Entry not found: {entry_id}")
        
        # Build the corrected entry fields from the original
        now_utc = datetime.now(timezone.utc).isoformat()
        manual_event_id = f"manual:{_generate_ulid()}"
        promotion_rule = f"correction.{correction_type}"
        
        # Start with original values
        summary = original["summary"]
        tags = json.loads(original.get("tags_json", "[]"))
        category = original["category"]
        entry_type_val = original["entry_type"]
        outcome = original["outcome"]
        importance_score = original["importance_score"]
        
        # Apply corrections based on type
        if correction_type == "summary":
            if not corrected_summary:
                raise ValueError("corrected_summary is required for summary corrections")
            summary = corrected_summary
        elif correction_type == "tags":
            if corrected_tags is None:
                raise ValueError("corrected_tags is required for tag corrections")
            tags = corrected_tags
        elif correction_type == "category":
            if corrected_category:
                category = corrected_category
            if corrected_entry_type:
                entry_type_val = corrected_entry_type
        elif correction_type == "outcome":
            if not corrected_outcome:
                raise ValueError("corrected_outcome is required for outcome corrections")
            outcome = corrected_outcome
        elif correction_type == "retraction":
            # Retraction semantics (Packet F §6.4 / DESIGN_DELTA §6.4)
            retraction_reason = corrected_summary or "No reason provided"
            summary = f"[RETRACTED] {original['summary']} — Reason: {retraction_reason}"
            outcome = "abandoned"
            importance_score = 1
        
        # Insert the correcting entry (chain validation happens in insert_work_log_entry)
        return self.insert_work_log_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            category=category,
            entry_type=entry_type_val,
            summary=summary,
            source_event_id=manual_event_id,
            source_event_type="manual.correction",
            source_adapter="manual_correction",
            source_event_ts_utc=now_utc,
            promotion_rule=promotion_rule,
            session_id=original.get("session_id"),
            workflow_phase=original.get("workflow_phase"),
            details=json.loads(original["details_json"]) if original.get("details_json") else None,
            reasoning=original.get("reasoning"),
            outcome=outcome,
            importance_score=importance_score,
            tags=tags,
            linked_decisions=json.loads(original["linked_decisions_json"]) if original.get("linked_decisions_json") else None,
            linked_files=json.loads(original["linked_files_json"]) if original.get("linked_files_json") else None,
            linked_commits=json.loads(original["linked_commits_json"]) if original.get("linked_commits_json") else None,
            linked_chat_range=json.loads(original["linked_chat_range_json"]) if original.get("linked_chat_range_json") else None,
            parent_entry_id=original.get("parent_entry_id"),
            supersedes_entry_id=entry_id,
            duration_sec=original.get("duration_sec"),
        )

    def retract_entry(
        self,
        workspace_id: str,
        instance_id: str,
        entry_id: str,
        reason: str,
    ) -> str:
        """Retract an entry. Convenience wrapper around correct_entry.
        
        Per Packet F §4.3 / DESIGN_DELTA §6.4.
        
        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            entry_id: ID of the entry to retract (must be chain head)
            reason: Explanation for why the entry is being retracted
            
        Returns:
            The retraction entry's ID
        """
        return self.correct_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            entry_id=entry_id,
            correction_type="retraction",
            corrected_summary=reason,
        )
