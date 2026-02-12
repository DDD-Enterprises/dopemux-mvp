"""
Copilot CLI capture adapter.

Integrates copilot_transcript_ingester with Dopemux emit_capture_event() for
content-addressed deduplication and consistent Chronicle schema.
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add services to path for import
services_path = Path(__file__).parent.parent.parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from copilot_transcript_ingester.parser import JSONLParser
from copilot_transcript_ingester.mapper import EventTypeMapper

from ..capture_client import emit_capture_event, CaptureResult


class CopilotCaptureAdapter:
    """
    Adapter for Copilot CLI transcripts.

    Parses JSONL from ~/.copilot/session-state/{UUID}/events.jsonl and
    emits to Chronicle via emit_capture_event() for content-addressed dedup.
    """

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        copilot_session_dir: Optional[Path] = None,
    ):
        """
        Initialize Copilot adapter.

        Args:
            repo_root: Project repository root (default: auto-detect)
            copilot_session_dir: Copilot session state directory
                (default: ~/.copilot/session-state)
        """
        self.repo_root = repo_root
        self.copilot_session_dir = copilot_session_dir or (
            Path.home() / ".copilot" / "session-state"
        )

    def ingest_session(
        self,
        session_id: str,
        since: Optional[datetime] = None,
    ) -> dict:
        """
        Ingest Copilot session events into Chronicle.

        Args:
            session_id: Copilot session UUID
            since: Optional timestamp filter - only ingest events after this

        Returns:
            Stats dict: {
                "total": total events parsed,
                "inserted": successfully inserted,
                "skipped": skipped (unmapped types),
                "deduplicated": already existed
            }
        """
        # Locate session transcript
        session_path = self.copilot_session_dir / session_id
        events_file = session_path / "events.jsonl"

        if not events_file.exists():
            raise FileNotFoundError(f"Session transcript not found: {events_file}")

        # Parse JSONL events
        parser = JSONLParser(str(events_file))
        events = list(parser.parse_events(since=since))

        stats = {
            "total": len(events),
            "inserted": 0,
            "skipped": 0,
            "deduplicated": 0,
        }

        # Emit each event via emit_capture_event()
        for copilot_event in events:
            copilot_type = copilot_event.get("type")

            # Map to Chronicle event type
            chronicle_type = EventTypeMapper.map_event_type(copilot_type)
            if not chronicle_type:
                stats["skipped"] += 1
                continue

            # Build event envelope for emit_capture_event()
            # Store Copilot-native ID as metadata, use content-addressed event_id
            payload = EventTypeMapper.extract_payload(copilot_event)

            event = {
                "event_type": chronicle_type,
                "ts_utc": copilot_event.get("timestamp"),
                "session_id": session_id,  # Copilot session ID
                "source": "copilot-cli",
                "payload": payload,
                # Do NOT set event_id here - let emit_capture_event() generate it
                # for content-addressed deduplication
            }

            # Emit via canonical capture function
            try:
                result = emit_capture_event(
                    event,
                    mode="cli",  # Copilot ingestion is a CLI operation
                    repo_root=self.repo_root,
                    emit_event_bus=False,  # Don't emit to event bus for batch ingestion
                )

                if result.inserted:
                    stats["inserted"] += 1
                else:
                    stats["deduplicated"] += 1

            except Exception as e:
                print(f"Warning: Failed to emit event {copilot_event.get('id')}: {e}")
                stats["skipped"] += 1

        return stats

    def list_sessions(self) -> list[dict]:
        """
        List available Copilot sessions.

        Returns:
            List of session info dicts with:
            - session_id: UUID
            - event_count: Number of events
            - start_timestamp: Session start time
        """
        if not self.copilot_session_dir.exists():
            return []

        sessions = []
        for session_path in self.copilot_session_dir.iterdir():
            if not session_path.is_dir():
                continue

            events_file = session_path / "events.jsonl"
            if not events_file.exists():
                continue

            try:
                parser = JSONLParser(str(events_file))
                count = parser.count_events()
                metadata = parser.get_session_metadata()

                sessions.append({
                    "session_id": session_path.name,
                    "event_count": count,
                    "start_timestamp": metadata.get("start_timestamp") if metadata else None,
                })
            except Exception:
                continue

        return sorted(sessions, key=lambda s: s.get("start_timestamp") or "", reverse=True)
