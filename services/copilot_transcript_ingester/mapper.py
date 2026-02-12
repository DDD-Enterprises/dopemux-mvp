"""
Event type mapping from Copilot CLI JSONL to Chronicle event types.

Maps Copilot event.type → chronicle event_type for raw_activity_events table.
"""

from typing import Optional
import json


class EventTypeMapper:
    """Maps Copilot CLI event types to Chronicle event types."""

    # Event type mappings from Decision #2
    COPILOT_TO_CHRONICLE = {
        "session.start": "copilot:session:start",
        "session.end": "copilot:session:end",
        "user.message": "copilot:input:user_message",
        "assistant.turn_start": "copilot:ai:turn_start",
        "assistant.message": "copilot:ai:response_start",
        "assistant.turn_end": "copilot:ai:turn_end",
        "tool.execution_start": "copilot:tool:invoke_start",
        "tool.execution_result": "copilot:tool:invoke_complete",
        "tool.execution_complete": "copilot:tool:invoke_complete",
        "tool.error": "copilot:tool:error",
        "context.window_updated": "copilot:context:updated",
        "context.truncated": "copilot:context:truncated",
        "error": "copilot:error",
        "checkpoint": "copilot:checkpoint",
    }

    @classmethod
    def map_event_type(cls, copilot_type: str) -> Optional[str]:
        """
        Map a Copilot event type to Chronicle event type.

        Args:
            copilot_type: Event type from Copilot JSONL (e.g., "user.message")

        Returns:
            Chronicle event type string, or None if mapping not found
        """
        return cls.COPILOT_TO_CHRONICLE.get(copilot_type)

    @classmethod
    def extract_payload(cls, copilot_event: dict) -> dict:
        """
        Extract payload from Copilot event.

        Copilot event structure:
        {
            "id": "event-uuid",
            "type": "user.message",
            "timestamp": "2025-02-12T10:15:30Z",
            "parentId": "parent-uuid",
            "data": {...}
        }

        Returns payload dict suitable for Chronicle raw_activity_events.payload_json
        """
        payload = {
            "copilot_event_id": copilot_event.get("id"),
            "copilot_type": copilot_event.get("type"),
            "copilot_parent_id": copilot_event.get("parentId"),
            "data": copilot_event.get("data", {}),
        }
        return payload

    @classmethod
    def is_mappable(cls, copilot_type: str) -> bool:
        """Check if Copilot event type has a Chronicle mapping."""
        return copilot_type in cls.COPILOT_TO_CHRONICLE
