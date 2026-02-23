"""
Chronicle ingester - writes Copilot events to Dope-Memory Chronicle.

Inserts parsed Copilot events into raw_activity_events table with proper
provenance metadata and content-addressed deduplication via event_id.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from .mapper import EventTypeMapper


class ChronicleIngester:
    """Ingests Copilot events into Chronicle database."""

    def __init__(self, db_path: str, workspace_id: str, instance_id: str):
        """
        Initialize ingester.

        Args:
            db_path: Path to Chronicle SQLite database
            workspace_id: Workspace identifier (e.g., /Users/hue/code/dopemux-mvp)
            instance_id: Instance identifier (e.g., "copilot-cli-macos")
        """
        self.db_path = Path(db_path)
        self.workspace_id = workspace_id
        self.instance_id = instance_id
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open database connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def ingest_events(
        self,
        events: List[dict],
        session_id: str,
        source: str = "copilot-cli",
    ) -> int:
        """
        Ingest list of Copilot events into Chronicle.

        Args:
            events: List of parsed Copilot events
            session_id: Session identifier from Copilot
            source: Event source identifier (default: "copilot-cli")

        Returns:
            Number of events successfully ingested
        """
        if not self.connection:
            raise RuntimeError("Not connected to database. Call connect() first.")

        inserted_count = 0
        skipped_count = 0

        cursor = self.connection.cursor()
        batch_data = []
        created_at_utc = datetime.utcnow().isoformat() + "Z"

        for event in events:
            try:
                # Map Copilot event type to Chronicle event type
                copilot_type = event.get("type")
                chronicle_type = EventTypeMapper.map_event_type(copilot_type)

                if not chronicle_type:
                    print(f"Skipping unmapped event type: {copilot_type}")
                    skipped_count += 1
                    continue

                # Extract timestamp
                ts_utc = event.get("timestamp", datetime.utcnow().isoformat() + "Z")

                # Build payload
                payload = EventTypeMapper.extract_payload(event)

                # Generate event ID (content-addressed with copilot event ID)
                event_id = event.get("id", str(uuid.uuid4()))

                batch_data.append((
                    event_id,
                    self.workspace_id,
                    self.instance_id,
                    session_id,
                    ts_utc,
                    chronicle_type,
                    source,
                    json.dumps(payload),
                    "strict",  # Default redaction level
                    7,  # 7-day TTL for raw events
                    created_at_utc,
                ))

            except Exception as e:
                print(f"Error preparing event: {e}")
                skipped_count += 1
                continue

        if batch_data:
            cursor.executemany(
                """
                INSERT OR IGNORE INTO raw_activity_events (
                    id, workspace_id, instance_id, session_id,
                    ts_utc, event_type, source,
                    payload_json, redaction_level,
                    ttl_days, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch_data,
            )
            # rowcount is the number of rows actually inserted (excluding ignored duplicates)
            # if rowcount is -1 (unsupported), we fallback to len(batch_data)
            affected = cursor.rowcount
            if affected != -1:
                inserted_count = affected
                skipped_count += (len(batch_data) - affected)
            else:
                inserted_count = len(batch_data)

        # Commit transaction
        self.connection.commit()

        return inserted_count

    def ingest_from_jsonl(
        self,
        jsonl_path: str,
        session_id: str,
    ) -> dict:
        """
        Ingest events directly from JSONL file.

        Args:
            jsonl_path: Path to events.jsonl file
            session_id: Session identifier

        Returns:
            Stats dict: {
                "total": total events processed,
                "inserted": successfully inserted,
                "skipped": skipped events,
                "errors": error count
            }
        """
        from .parser import JSONLParser

        parser = JSONLParser(jsonl_path)
        events = list(parser.parse_events())

        inserted = self.ingest_events(events, session_id)

        return {
            "total": len(events),
            "inserted": inserted,
            "skipped": len(events) - inserted,
            "errors": 0,
        }

    def get_ingestion_stats(
        self, session_id: Optional[str] = None
    ) -> dict:
        """
        Get statistics about ingested events.

        Args:
            session_id: Optional - filter stats to specific session

        Returns:
            Stats dict with event counts by type
        """
        if not self.connection:
            raise RuntimeError("Not connected to database. Call connect() first.")

        cursor = self.connection.cursor()

        query = """
            SELECT event_type, COUNT(*) as count
            FROM raw_activity_events
            WHERE workspace_id = ? AND instance_id = ?
        """
        params = [self.workspace_id, self.instance_id]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " GROUP BY event_type ORDER BY count DESC"

        cursor.execute(query, params)
        results = cursor.fetchall()

        return {
            "session_id": session_id,
            "workspace_id": self.workspace_id,
            "instance_id": self.instance_id,
            "event_counts": {row[0]: row[1] for row in results},
            "total_events": sum(row[1] for row in results),
        }
