"""
JSONL parser for Copilot CLI transcript events.

Reads ~/.copilot/session-state/{SESSION_ID}/events.jsonl
Each line is a JSON object representing a single event.
"""

import json
from typing import Iterator, Optional, Tuple
from datetime import datetime
from pathlib import Path


class JSONLParser:
    """Parse JSONL transcript files from Copilot CLI."""

    def __init__(self, file_path: str):
        """
        Initialize parser with path to events.jsonl file.

        Args:
            file_path: Absolute path to events.jsonl
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")

    def parse_events(
        self, since: Optional[datetime] = None
    ) -> Iterator[dict]:
        """
        Parse JSONL events from file.

        Args:
            since: Optional datetime filter - only return events after this time

        Yields:
            Parsed event dictionaries with structure:
            {
                "id": "event-uuid",
                "type": "user.message",
                "timestamp": "2025-02-12T10:15:30Z",
                "parentId": "parent-uuid",
                "data": {...}
            }
        """
        with open(self.file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    # Skip empty lines
                    continue

                try:
                    event = json.loads(line)

                    # Validate event structure
                    if not isinstance(event, dict) or "type" not in event:
                        print(
                            f"Warning: Invalid event at line {line_num}, "
                            f"skipping (missing 'type' field)"
                        )
                        continue

                    # Filter by timestamp if provided
                    if since:
                        event_ts = self._parse_timestamp(event.get("timestamp"))
                        if event_ts and event_ts < since:
                            continue

                    yield event

                except json.JSONDecodeError as e:
                    print(
                        f"Warning: Failed to parse JSON at line {line_num}: {e}"
                    )
                    continue

    def get_session_metadata(self) -> Optional[dict]:
        """
        Extract session metadata from first event (usually session.start).

        Returns:
            Session metadata dict with keys like session_id, start_time, etc.
        """
        with open(self.file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if event.get("type") == "session.start":
                        return {
                            "session_id": event.get("id"),
                            "start_timestamp": event.get("timestamp"),
                            "data": event.get("data", {}),
                        }
                except json.JSONDecodeError:
                    continue
        return None

    def count_events(self) -> int:
        """Count total events in transcript file."""
        count = 0
        with open(self.file_path, "r") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    @staticmethod
    def _parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 timestamp string to datetime."""
        if not ts_str:
            return None
        try:
            # Handle both formats: with and without 'Z'
            ts_str = ts_str.rstrip("Z")
            if "T" in ts_str:
                return datetime.fromisoformat(ts_str)
        except (ValueError, AttributeError):
            pass
        return None
