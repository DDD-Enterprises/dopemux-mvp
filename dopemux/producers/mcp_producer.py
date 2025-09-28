"""
MCP Event Producer

Automatically emits events for MCP tool invocations and server interactions.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from ..event_bus import EventBus, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata


class MCPEventProducer:
    """Producer that emits events for MCP tool calls and server interactions."""

    def __init__(self, event_bus: EventBus, instance_id: str = "default"):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.tool_start_times: Dict[str, float] = {}

    def _calculate_cognitive_load(self, tool_name: str, duration_ms: int) -> CognitiveLoad:
        """Calculate cognitive load based on tool type and execution time."""
        # High cognitive load tools
        high_load_tools = [
            "mcp__zen__thinkdeep",
            "mcp__zen__debug",
            "mcp__zen__planner",
            "mcp__zen__consensus"
        ]

        # Medium cognitive load tools
        medium_load_tools = [
            "mcp__zen__codereview",
            "mcp__zen__analyze",
            "mcp__zen__refactor"
        ]

        # Quick tools are usually low cognitive load
        if duration_ms < 1000:  # Under 1 second
            return CognitiveLoad.LOW

        if tool_name in high_load_tools or duration_ms > 30000:  # Over 30 seconds
            return CognitiveLoad.HIGH
        elif tool_name in medium_load_tools or duration_ms > 5000:  # Over 5 seconds
            return CognitiveLoad.MEDIUM
        else:
            return CognitiveLoad.LOW

    def _get_tool_priority(self, tool_name: str) -> Priority:
        """Determine event priority based on tool importance."""
        critical_tools = [
            "mcp__zen__debug",
            "Bash",  # System commands
            "Write", "Edit", "MultiEdit"  # Code modifications
        ]

        high_priority_tools = [
            "mcp__zen__thinkdeep",
            "mcp__zen__planner",
            "mcp__conport__log_decision",
            "mcp__conport__log_progress"
        ]

        if tool_name in critical_tools:
            return Priority.CRITICAL
        elif tool_name in high_priority_tools:
            return Priority.HIGH
        else:
            return Priority.NORMAL

    async def on_tool_call_start(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Called when an MCP tool call begins."""
        call_id = f"{tool_name}_{int(time.time() * 1000)}"
        self.tool_start_times[call_id] = time.time()

        # Emit start event for long-running tools
        long_running_tools = [
            "mcp__zen__thinkdeep",
            "mcp__zen__debug",
            "mcp__zen__planner"
        ]

        if tool_name in long_running_tools:
            event = DopemuxEvent.create(
                event_type="mcp.tool.started",
                namespace=f"instance.{self.instance_id}.mcp",
                payload={
                    "call_id": call_id,
                    "tool": tool_name,
                    "arguments": self._sanitize_args(args),
                    "started_at": datetime.now().isoformat()
                },
                source="mcp.producer",
                priority=self._get_tool_priority(tool_name),
                adhd_metadata=ADHDMetadata(
                    cognitive_load=CognitiveLoad.MEDIUM,
                    attention_required=True,
                    interruption_safe=False,
                    focus_context="tool_execution"
                ),
                targets=[f"instance.{self.instance_id}"],
                filters=["mcp.tool_tracking"]
            )
            await self.event_bus.publish(event)

        return call_id

    async def on_tool_call_complete(
        self,
        call_id: str,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        error: Optional[str] = None
    ):
        """Called when an MCP tool call completes."""
        # Calculate execution time
        start_time = self.tool_start_times.pop(call_id, time.time())
        duration_ms = int((time.time() - start_time) * 1000)

        # Determine event type
        event_type = "mcp.tool.error" if error else "mcp.tool.completed"

        # Prepare payload
        payload = {
            "call_id": call_id,
            "tool": tool_name,
            "arguments": self._sanitize_args(args),
            "duration_ms": duration_ms,
            "completed_at": datetime.now().isoformat(),
            "success": error is None
        }

        if error:
            payload["error"] = str(error)[:500]  # Truncate long errors
        else:
            payload["result_summary"] = self._summarize_result(result)

        # Create event
        event = DopemuxEvent.create(
            event_type=event_type,
            namespace=f"instance.{self.instance_id}.mcp",
            payload=payload,
            source="mcp.producer",
            priority=Priority.CRITICAL if error else self._get_tool_priority(tool_name),
            adhd_metadata=ADHDMetadata(
                cognitive_load=self._calculate_cognitive_load(tool_name, duration_ms),
                attention_required=bool(error),  # Errors need attention
                interruption_safe=True,
                focus_context="tool_completion",
                batching_allowed=not bool(error)  # Don't batch errors
            ),
            targets=[f"instance.{self.instance_id}"],
            filters=["mcp.tool_tracking", "mcp.completion"]
        )

        await self.event_bus.publish(event)

    async def on_server_connection_change(self, server_name: str, status: str, error: Optional[str] = None):
        """Called when MCP server connection status changes."""
        event = DopemuxEvent.create(
            event_type="mcp.server.connection.changed",
            namespace=f"instance.{self.instance_id}.mcp.server",
            payload={
                "server": server_name,
                "status": status,  # connected, disconnected, error
                "timestamp": datetime.now().isoformat(),
                "error": error if error else None
            },
            source="mcp.producer",
            priority=Priority.HIGH if status == "error" else Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MEDIUM if status == "error" else CognitiveLoad.LOW,
                attention_required=status == "error",
                interruption_safe=status != "error",
                focus_context="infrastructure"
            ),
            targets=[f"instance.{self.instance_id}", "shared.infrastructure"],
            filters=["mcp.infrastructure", "system.monitoring"]
        )

        await self.event_bus.publish(event)

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from arguments."""
        sanitized = {}
        sensitive_keys = [
            "password", "token", "key", "secret", "credential",
            "auth", "api_key", "access_token"
        ]

        for key, value in args.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                # Truncate very long strings
                sanitized[key] = value[:1000] + "... [TRUNCATED]"
            else:
                sanitized[key] = value

        return sanitized

    def _summarize_result(self, result: Any) -> str:
        """Create a brief summary of the tool result."""
        if result is None:
            return "No result"

        if isinstance(result, str):
            return result[:200] + ("..." if len(result) > 200 else "")
        elif isinstance(result, dict):
            if "error" in result:
                return f"Error: {str(result['error'])[:100]}"
            elif "success" in result:
                return "Operation completed successfully"
            else:
                return f"Dict with {len(result)} keys"
        elif isinstance(result, (list, tuple)):
            return f"Collection with {len(result)} items"
        else:
            return f"Result: {type(result).__name__}"

    async def emit_productivity_metric(self, metric_type: str, value: float, context: Dict[str, Any]):
        """Emit productivity metrics for ADHD analysis."""
        event = DopemuxEvent.create(
            event_type="mcp.productivity.metric",
            namespace=f"instance.{self.instance_id}.analytics",
            payload={
                "metric_type": metric_type,  # focus_duration, tool_efficiency, context_switches
                "value": value,
                "context": context,
                "timestamp": datetime.now().isoformat()
            },
            source="mcp.producer",
            priority=Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MINIMAL,
                attention_required=False,
                interruption_safe=True,
                focus_context="analytics",
                batching_allowed=True
            ),
            targets=["shared.analytics"],
            filters=["analytics.productivity", "adhd.metrics"]
        )

        await self.event_bus.publish(event)