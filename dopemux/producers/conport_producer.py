"""
ConPort Event Producer

Automatically emits events for ConPort operations and context changes.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..event_bus import EventBus, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata


class ConPortEventProducer:
    """Producer that emits events for ConPort context operations."""

    def __init__(self, event_bus: EventBus, instance_id: str = "default", workspace_id: str = ""):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.workspace_id = workspace_id

    async def on_decision_logged(
        self,
        decision_id: int,
        summary: str,
        rationale: str,
        tags: List[str],
        implementation_details: Optional[str] = None
    ):
        """Called when a decision is logged in ConPort."""
        # Determine if this is an architectural decision (higher cognitive load)
        is_architectural = any(tag in ["architecture", "design", "pattern"] for tag in tags)

        event = DopemuxEvent.create(
            event_type="conport.decision.logged",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "decision_id": decision_id,
                "summary": summary,
                "rationale": rationale[:500],  # Truncate long rationale
                "tags": tags,
                "implementation_details": implementation_details[:300] if implementation_details else None,
                "workspace_id": self.workspace_id,
                "logged_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.HIGH if is_architectural else Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.HIGH if is_architectural else CognitiveLoad.MEDIUM,
                attention_required=is_architectural,
                interruption_safe=not is_architectural,
                focus_context="decision_making",
                batching_allowed=not is_architectural
            ),
            targets=[f"instance.{self.instance_id}", "shared.team"],
            filters=["conport.decisions", "team.awareness"]
        )

        await self.event_bus.publish(event)

    async def on_progress_updated(
        self,
        progress_id: int,
        description: str,
        old_status: str,
        new_status: str,
        linked_item_id: Optional[str] = None
    ):
        """Called when progress status is updated."""
        is_completion = new_status.upper() == "DONE"
        is_blocking = new_status.upper() == "BLOCKED"

        event = DopemuxEvent.create(
            event_type="conport.progress.updated",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "progress_id": progress_id,
                "description": description,
                "old_status": old_status,
                "new_status": new_status,
                "linked_item_id": linked_item_id,
                "workspace_id": self.workspace_id,
                "updated_at": datetime.now().isoformat(),
                "is_completion": is_completion,
                "is_blocking": is_blocking
            },
            source="conport.producer",
            priority=Priority.HIGH if is_blocking else Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MEDIUM if is_blocking else CognitiveLoad.LOW,
                attention_required=is_blocking,
                interruption_safe=not is_blocking,
                focus_context="progress_tracking",
                batching_allowed=not (is_completion or is_blocking)
            ),
            targets=[f"instance.{self.instance_id}", "shared.team"] if is_completion else [f"instance.{self.instance_id}"],
            filters=["conport.progress", "productivity.tracking"]
        )

        await self.event_bus.publish(event)

        # Emit celebration event for completions
        if is_completion:
            await self._emit_completion_celebration(description)

    async def _emit_completion_celebration(self, description: str):
        """Emit a low-pressure celebration event for ADHD motivation."""
        event = DopemuxEvent.create(
            event_type="conport.progress.celebration",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "message": f"🎉 Completed: {description}",
                "celebration_type": "task_completion",
                "workspace_id": self.workspace_id,
                "completed_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MINIMAL,
                attention_required=False,
                interruption_safe=True,
                focus_context="positive_reinforcement",
                batching_allowed=True
            ),
            targets=[f"instance.{self.instance_id}"],
            filters=["adhd.celebration", "motivation.positive"]
        )

        await self.event_bus.publish(event)

    async def on_system_pattern_logged(
        self,
        pattern_id: int,
        name: str,
        description: str,
        tags: List[str]
    ):
        """Called when a system pattern is logged."""
        event = DopemuxEvent.create(
            event_type="conport.pattern.logged",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "pattern_id": pattern_id,
                "name": name,
                "description": description[:500],
                "tags": tags,
                "workspace_id": self.workspace_id,
                "logged_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MEDIUM,
                attention_required=False,
                interruption_safe=True,
                focus_context="knowledge_capture",
                batching_allowed=True
            ),
            targets=[f"instance.{self.instance_id}", "shared.team"],
            filters=["conport.patterns", "knowledge.sharing"]
        )

        await self.event_bus.publish(event)

    async def on_context_updated(
        self,
        context_type: str,  # "product_context" or "active_context"
        changes: Dict[str, Any],
        version: Optional[int] = None
    ):
        """Called when product or active context is updated."""
        is_active_context = context_type == "active_context"

        event = DopemuxEvent.create(
            event_type="conport.context.updated",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "context_type": context_type,
                "changes": self._sanitize_context_changes(changes),
                "version": version,
                "workspace_id": self.workspace_id,
                "updated_at": datetime.now().isoformat(),
                "change_count": len(changes)
            },
            source="conport.producer",
            priority=Priority.NORMAL if is_active_context else Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW,
                attention_required=False,
                interruption_safe=True,
                focus_context="context_management",
                batching_allowed=True
            ),
            targets=[f"instance.{self.instance_id}"],
            filters=["conport.context", "session.management"]
        )

        await self.event_bus.publish(event)

    async def on_custom_data_logged(
        self,
        category: str,
        key: str,
        value: Any,
        operation: str = "create"  # create, update, delete
    ):
        """Called when custom data is logged to ConPort."""
        # Determine priority based on category
        high_priority_categories = ["sprint_goals", "blockers", "risks"]
        is_high_priority = category in high_priority_categories

        event = DopemuxEvent.create(
            event_type="conport.custom_data.logged",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "category": category,
                "key": key,
                "value_summary": self._summarize_value(value),
                "operation": operation,
                "workspace_id": self.workspace_id,
                "logged_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.HIGH if is_high_priority else Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MEDIUM if is_high_priority else CognitiveLoad.LOW,
                attention_required=is_high_priority and operation in ["create", "delete"],
                interruption_safe=not is_high_priority,
                focus_context="data_management",
                batching_allowed=not is_high_priority
            ),
            targets=[f"instance.{self.instance_id}"],
            filters=["conport.data", f"category.{category}"]
        )

        await self.event_bus.publish(event)

    async def on_search_performed(
        self,
        search_type: str,  # semantic, fts, glossary
        query: str,
        result_count: int,
        execution_time_ms: int
    ):
        """Called when a search is performed in ConPort."""
        event = DopemuxEvent.create(
            event_type="conport.search.performed",
            namespace=f"instance.{self.instance_id}.conport.analytics",
            payload={
                "search_type": search_type,
                "query": query[:100],  # Truncate long queries
                "result_count": result_count,
                "execution_time_ms": execution_time_ms,
                "workspace_id": self.workspace_id,
                "searched_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MINIMAL,
                attention_required=False,
                interruption_safe=True,
                focus_context="information_retrieval",
                batching_allowed=True
            ),
            targets=["shared.analytics"],
            filters=["analytics.search", "usage.tracking"]
        )

        await self.event_bus.publish(event)

    async def on_session_event(
        self,
        event_type: str,  # session_start, session_save, session_restore
        session_data: Dict[str, Any]
    ):
        """Called for session management events."""
        is_critical = event_type in ["session_save", "session_restore"]

        event = DopemuxEvent.create(
            event_type=f"conport.session.{event_type}",
            namespace=f"instance.{self.instance_id}.session",
            payload={
                "session_event": event_type,
                "session_data": self._sanitize_session_data(session_data),
                "workspace_id": self.workspace_id,
                "timestamp": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.HIGH if is_critical else Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW,
                attention_required=False,
                interruption_safe=True,
                focus_context="session_management",
                batching_allowed=not is_critical
            ),
            targets=[f"instance.{self.instance_id}", "shared.session"] if is_critical else [f"instance.{self.instance_id}"],
            filters=["session.management", "context.preservation"]
        )

        await self.event_bus.publish(event)

    def _sanitize_context_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive or overly verbose context data."""
        sanitized = {}
        max_value_length = 200

        for key, value in changes.items():
            if isinstance(value, str) and len(value) > max_value_length:
                sanitized[key] = value[:max_value_length] + "... [TRUNCATED]"
            elif isinstance(value, dict):
                sanitized[key] = f"Dict with {len(value)} keys"
            elif isinstance(value, list):
                sanitized[key] = f"List with {len(value)} items"
            else:
                sanitized[key] = value

        return sanitized

    def _summarize_value(self, value: Any) -> str:
        """Create a brief summary of custom data value."""
        if value is None:
            return "null"
        elif isinstance(value, str):
            return value[:100] + ("..." if len(value) > 100 else "")
        elif isinstance(value, dict):
            return f"Object with keys: {list(value.keys())[:5]}"
        elif isinstance(value, list):
            return f"Array with {len(value)} items"
        else:
            return str(type(value).__name__)

    def _sanitize_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive session information."""
        # Only include metadata, not actual content
        return {
            "context_count": len(session_data.get("contexts", [])),
            "decision_count": len(session_data.get("decisions", [])),
            "progress_count": len(session_data.get("progress", [])),
            "session_duration": session_data.get("duration_minutes", 0),
            "focus_context": session_data.get("focus_context", "unknown")
        }

    async def on_context_accessed(
        self,
        context_type: str,
        access_reason: str,
        user_id: Optional[str] = None
    ):
        """Called when context is accessed for reading."""
        event = DopemuxEvent.create(
            event_type="conport.context.accessed",
            namespace=f"instance.{self.instance_id}.conport",
            payload={
                "context_type": context_type,
                "access_reason": access_reason,
                "user_id": user_id,
                "workspace_id": self.workspace_id,
                "accessed_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MINIMAL,
                attention_required=False,
                interruption_safe=True,
                focus_context="information_retrieval",
                batching_allowed=True
            ),
            targets=[f"instance.{self.instance_id}"],
            filters=["conport.access", "analytics.usage"]
        )

        await self.event_bus.publish(event)

    async def emit_focus_state_change(
        self,
        old_state: str,
        new_state: str,
        context: Dict[str, Any]
    ):
        """Emit event when user's focus state changes (for ADHD optimization)."""
        event = DopemuxEvent.create(
            event_type="conport.focus.state_changed",
            namespace=f"instance.{self.instance_id}.adhd",
            payload={
                "old_state": old_state,  # deep, scattered, transitioning
                "new_state": new_state,
                "context": context,
                "workspace_id": self.workspace_id,
                "changed_at": datetime.now().isoformat()
            },
            source="conport.producer",
            priority=Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW,
                attention_required=False,
                interruption_safe=True,
                focus_context="attention_management",
                batching_allowed=False  # Don't batch focus changes
            ),
            targets=[f"instance.{self.instance_id}"],
            filters=["adhd.focus", "attention.tracking"]
        )

        await self.event_bus.publish(event)