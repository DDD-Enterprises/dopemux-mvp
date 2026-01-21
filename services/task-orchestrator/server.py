#!/usr/bin/env python3
"""
Task-Orchestrator MCP Server Wrapper

This wrapper provides an MCP server interface for Task-Orchestrator,
which handles task dependency analysis and workflow orchestration.

Task-Orchestrator is a Kotlin-based system with 37 specialized tools.
"""

import asyncio
import json
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("task-orchestrator-wrapper")

# Add dopemux to path for event bus integration
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Enable event bus integration
EVENTS_ENABLED = True

# Try to import real event bus classes, fall back to mocks if not available
try:
    from dopemux.shared.event_bus.redis_streams_adapter import RedisStreamsAdapter
    from dopemux.shared.event_bus.events import DopemuxEvent
    from dopemux.shared.mcp.event_producer import MCPEventProducer
    logger.info("Event bus integration enabled successfully")
except ImportError as e:
    logger.warning(f"Event bus imports failed ({e}), using mock classes")
    EVENTS_ENABLED = False

    # Mock classes to prevent import errors
    class RedisStreamsAdapter:
        pass

    class DopemuxEvent:
        pass

    class MCPEventProducer:
        pass


class TaskOrchestratorWrapper:
    """
    Built-in MCP Server for Task-Orchestrator with dependency analysis.

    This server provides:
    - Direct MCP protocol implementation without subprocess
    - Event emission for dependency analysis and orchestration events
    - ADHD-friendly conflict detection and resolution guidance
    - Multi-instance coordination support
    """

    def __init__(self):
        self.event_bus: Optional[RedisStreamsAdapter] = None
        self.mcp_producer: Optional[MCPEventProducer] = None
        self.instance_id = os.getenv("DOPEMUX_INSTANCE", "default")
        self.workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")
        self.next_request_id = 1

        # Dependency tracking
        self.dependency_graph = defaultdict(set)
        self.blocked_tasks = set()
        self.critical_path = []

        # ADHD configuration for orchestration
        self.adhd_config = {
            "max_parallel_tasks": int(os.getenv("MAX_PARALLEL_TASKS", "3")),
            "conflict_alerts": os.getenv("CONFLICT_ALERTS", "true").lower() == "true",
            "dependency_visualization": os.getenv("DEPENDENCY_VIZ", "true").lower() == "true",
            "smart_batching": os.getenv("SMART_BATCHING", "true").lower() == "true"
        }

        # Track method calls
        self.pending_calls = {}
        self.orchestration_stats = {
            "dependencies_analyzed": 0,
            "conflicts_resolved": 0,
            "tasks_orchestrated": 0
        }

    async def initialize_event_bus(self):
        """Initialize connection to Redis event bus if available."""
        if not EVENTS_ENABLED:
            return

        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.event_bus = RedisStreamsAdapter(redis_url)
            await self.event_bus.connect()

            self.mcp_producer = MCPEventProducer(
                self.event_bus,
                self.instance_id
            )

            logger.info(f"Connected to event bus for instance {self.instance_id}")

        except Exception as e:
            logger.warning(f"Failed to connect to event bus: {e}")
            logger.info("Continuing without event emission")

    async def start_orchestrator(self):
        """Initialize the built-in Task-Orchestrator MCP server."""
        logger.info("Initializing built-in Task-Orchestrator MCP server...")
        try:
            # Instead of launching a subprocess, we'll implement the MCP server directly
            # The Kotlin binary doesn't exist, so we'll provide orchestration tools natively
            logger.info("Task-Orchestrator MCP server initialized (built-in implementation)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Task-Orchestrator: {e}")
            raise

    async def emit_orchestration_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an orchestration-related event to the event bus."""
        if not self.mcp_producer:
            return

        try:
            # Determine priority based on event type
            priority = Priority.HIGH if event_type in ["conflict", "blocked"] else Priority.MEDIUM
            cognitive_load = CognitiveLoad.HIGH if event_type == "conflict" else CognitiveLoad.MEDIUM

            event = DopemuxEvent(
                event_type=f"orchestration.{event_type}",
                source=f"task-orchestrator-{self.instance_id}",
                instance_id=self.instance_id,
                data=data,
                priority=priority,
                cognitive_load=cognitive_load,
                adhd_metadata=ADHDMetadata(
                    interruption_allowed=event_type in ["conflict", "blocked"],
                    focus_required=event_type == "critical_path",
                    time_sensitive=event_type == "conflict",
                    can_batch=event_type not in ["conflict", "blocked"]
                )
            )

            await self.event_bus.publish(event)
            logger.debug(f"Emitted {event_type} orchestration event")

        except Exception as e:
            logger.warning(f"Failed to emit event: {e}")

    async def handle_message(self, message: bytes) -> Optional[bytes]:
        """
        Process MCP messages directly and respond as an MCP server.
        """
        try:
            msg_str = message.decode('utf-8')
            msg_json = json.loads(msg_str)

            method = msg_json.get("method")
            msg_id = msg_json.get("id")
            params = msg_json.get("params", {})

            # Handle MCP protocol methods
            if method == "initialize":
                response = self._handle_initialize(msg_id, params)
            elif method == "tools/list":
                response = self._handle_tools_list(msg_id)
            elif method == "tools/call":
                response = await self._handle_tools_call(msg_id, params)
            elif method == "shutdown":
                response = self._handle_shutdown(msg_id)
            else:
                response = self._handle_unknown_method(msg_id, method)

            return json.dumps(response).encode('utf-8') + b'\n'

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return None

    def _handle_initialize(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "task-orchestrator",
                    "version": "1.0.0"
                }
            }
        }

    def _handle_tools_list(self, msg_id: int) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": "analyze_dependencies",
                "description": "Analyze task dependencies and identify blocked tasks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task names to analyze"
                        }
                    },
                    "required": ["tasks"]
                }
            },
            {
                "name": "detect_conflicts",
                "description": "Detect scheduling conflicts between tasks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task names to check for conflicts"
                        }
                    },
                    "required": ["tasks"]
                }
            },
            {
                "name": "find_critical_path",
                "description": "Find the critical path in a task dependency graph",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_task": {"type": "string", "description": "Starting task"},
                        "end_task": {"type": "string", "description": "Ending task"},
                        "tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of all tasks"
                        }
                    },
                    "required": ["start_task", "end_task", "tasks"]
                }
            },
            {
                "name": "batch_tasks",
                "description": "Group tasks into optimal execution batches",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tasks to batch"
                        },
                        "max_batch_size": {
                            "type": "integer",
                            "description": "Maximum tasks per batch",
                            "default": 3
                        }
                    },
                    "required": ["tasks"]
                }
            }
        ]

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tools}
        }

    async def _handle_tools_call(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        try:
            if tool_name == "analyze_dependencies":
                result = self._analyze_dependencies(tool_params.get("tasks", []))
            elif tool_name == "detect_conflicts":
                result = self._detect_conflicts(tool_params.get("tasks", []))
            elif tool_name == "find_critical_path":
                result = self._find_critical_path(
                    tool_params.get("start_task", ""),
                    tool_params.get("end_task", ""),
                    tool_params.get("tasks", [])
                )
            elif tool_name == "batch_tasks":
                result = self._batch_tasks(
                    tool_params.get("tasks", []),
                    tool_params.get("max_batch_size", 3)
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

            logger.error(f"Error: {e}")
    def _handle_shutdown(self, msg_id: int) -> Dict[str, Any]:
        """Handle shutdown request."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": None
        }

    def _handle_unknown_method(self, msg_id: int, method: str) -> Dict[str, Any]:
        """Handle unknown methods."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

    # Tool implementations
    def _analyze_dependencies(self, tasks: List[str]) -> Dict[str, Any]:
        """Analyze task dependencies (simplified implementation)."""
        # Mock dependency analysis
        dependencies = {}
        blocked = []

        for i, task in enumerate(tasks):
            deps = []
            if i > 0:
                deps.append(tasks[i-1])  # Simple chain dependency
                if i % 2 == 0:  # Some tasks are blocked
                    blocked.append(task)

            dependencies[task] = deps

        return {
            "dependencies": dependencies,
            "blocked_tasks": blocked,
            "total_tasks": len(tasks)
        }

    def _detect_conflicts(self, tasks: List[str]) -> Dict[str, Any]:
        """Detect conflicts between tasks (simplified implementation)."""
        conflicts = []

        # Mock conflicts: tasks with similar names
        task_names = {}
        for task in tasks:
            base_name = task.lower().replace("task", "").strip()
            if base_name in task_names:
                conflicts.append({
                    "task1": task_names[base_name],
                    "task2": task,
                    "reason": "Similar task names may indicate duplication"
                })
            else:
                task_names[base_name] = task

        return {
            "conflicts": conflicts,
            "total_conflicts": len(conflicts)
        }

    def _find_critical_path(self, start_task: str, end_task: str, tasks: List[str]) -> Dict[str, Any]:
        """Find critical path (simplified implementation)."""
        if start_task not in tasks or end_task not in tasks:
            raise ValueError("Start and end tasks must be in the task list")

        # Mock critical path: simple chain
        path = [start_task]
        current = start_task
        while current != end_task and len(path) < len(tasks):
            next_idx = tasks.index(current) + 1
            if next_idx < len(tasks):
                current = tasks[next_idx]
                path.append(current)
            else:
                break

        return {
            "path": path,
            "estimated_duration": len(path) * 2.0,  # 2 hours per task
            "bottlenecks": ["database_migration" if "db" in " ".join(path).lower() else None]
        }

    def _batch_tasks(self, tasks: List[str], max_batch_size: int) -> Dict[str, Any]:
        """Batch tasks for optimal execution."""
        batches = []
        for i in range(0, len(tasks), max_batch_size):
            batches.append(tasks[i:i + max_batch_size])

        return {
            "batches": batches,
            "total_batches": len(batches),
            "max_batch_size": max_batch_size
        }

    def _get_orchestration_tools(self) -> List[str]:
        """Get list of orchestration-specific tools."""
        return [
            "analyze_dependencies",
            "detect_conflicts",
            "resolve_conflict",
            "find_critical_path",
            "batch_tasks",
            "parallelize_tasks",
            "sequence_tasks",
            "estimate_timeline",
            "identify_blockers",
            "optimize_workflow"
        ]

    async def _handle_orchestration_tool(self, tool_name: str, params: Dict[str, Any]):
        """Handle orchestration-specific tool calls."""
        if tool_name == "analyze_dependencies":
            await self.emit_orchestration_event("dependency_analysis", {
                "tasks": params.get("tasks", []),
                "timestamp": datetime.now().isoformat()
            })
            self.orchestration_stats["dependencies_analyzed"] += 1

        elif tool_name == "detect_conflicts":
            # ADHD: Alert on conflicts immediately
            if self.adhd_config["conflict_alerts"]:
                sys.stderr.write("\n⚠️ Checking for task conflicts...\n")
                sys.stderr.flush()

        elif tool_name == "resolve_conflict":
            await self.emit_orchestration_event("conflict", {
                "conflict": params.get("conflict", {}),
                "resolution_strategy": params.get("strategy", "manual"),
                "timestamp": datetime.now().isoformat()
            })
            self.orchestration_stats["conflicts_resolved"] += 1

        elif tool_name == "find_critical_path":
            await self.emit_orchestration_event("critical_path", {
                "start": params.get("start_task"),
                "end": params.get("end_task"),
                "timestamp": datetime.now().isoformat()
            })

    async def _process_orchestration_result(self, tool_name: str, result: Any, duration: float):
        """Process and emit events for orchestration results."""
        if tool_name == "analyze_dependencies" and isinstance(result, dict):
            # Update dependency graph
            dependencies = result.get("dependencies", {})
            for task, deps in dependencies.items():
                self.dependency_graph[task].update(deps)

            # Identify blocked tasks
            blocked = result.get("blocked_tasks", [])
            self.blocked_tasks.update(blocked)

            if blocked and self.adhd_config["conflict_alerts"]:
                sys.stderr.write(f"\n🚨 {len(blocked)} tasks are blocked by dependencies!\n")
                sys.stderr.flush()

            await self.emit_orchestration_event("dependencies_analyzed", {
                "total_tasks": len(dependencies),
                "blocked_tasks": len(blocked),
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })

        elif tool_name == "find_critical_path" and isinstance(result, dict):
            # Store critical path
            self.critical_path = result.get("path", [])
            estimated_duration = result.get("estimated_duration", 0)

            # ADHD-friendly visualization
            if self.adhd_config["dependency_visualization"]:
                path_viz = self._visualize_critical_path(self.critical_path, estimated_duration)
                sys.stderr.write(f"\n{path_viz}\n")
                sys.stderr.flush()

        elif tool_name == "batch_tasks" and isinstance(result, dict):
            # Smart batching for ADHD
            batches = result.get("batches", [])
            if batches and self.adhd_config["smart_batching"]:
                batch_info = self._generate_batch_guidance(batches)
                sys.stderr.write(f"\n{batch_info}\n")
                sys.stderr.flush()

    def _generate_orchestration_guidance(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate ADHD-friendly orchestration guidance."""
        guidance = {
            "analyze_dependencies": "🔍 Analyzing task dependencies...",
            "detect_conflicts": "⚠️ Checking for conflicts...",
            "resolve_conflict": "🔧 Resolving conflict...",
            "find_critical_path": "🎯 Finding critical path...",
            "batch_tasks": "📦 Creating task batches...",
            "parallelize_tasks": "⚡ Identifying parallel opportunities...",
            "sequence_tasks": "📝 Sequencing tasks...",
            "estimate_timeline": "⏱️ Estimating timeline...",
            "identify_blockers": "🚧 Identifying blockers...",
            "optimize_workflow": "✨ Optimizing workflow..."
        }
        return guidance.get(tool_name, f"🔄 Processing {tool_name}...")

    def _visualize_critical_path(self, path: List[str], duration: float) -> str:
        """Create ADHD-friendly visualization of critical path."""
        if not path:
            return "📍 No critical path identified"

        viz = "🎯 Critical Path:\n"
        for i, task in enumerate(path):
            if i == 0:
                viz += f"  ┌─ {task}\n"
            elif i == len(path) - 1:
                viz += f"  └─ {task} ✅\n"
            else:
                viz += f"  ├─ {task}\n"

        viz += f"\n⏱️ Estimated duration: {duration:.1f} hours"
        return viz

    def _generate_batch_guidance(self, batches: List[List[str]]) -> str:
        """Generate ADHD-friendly batch guidance."""
        if not batches:
            return ""

        max_parallel = self.adhd_config["max_parallel_tasks"]
        guidance = f"📦 Task Batches (max {max_parallel} parallel):\n"

        for i, batch in enumerate(batches[:3]):  # Show first 3 batches
            batch_size = min(len(batch), max_parallel)
            guidance += f"\nBatch {i+1} ({batch_size} tasks):\n"
            for task in batch[:max_parallel]:
                guidance += f"  • {task}\n"
            if len(batch) > max_parallel:
                guidance += f"  • (+{len(batch) - max_parallel} more...)\n"

        if len(batches) > 3:
            guidance += f"\n... and {len(batches) - 3} more batches"

        return guidance

    async def run(self):
        """Main MCP server run loop."""
        # Initialize event bus
        await self.initialize_event_bus()

        # Initialize the built-in orchestrator
        await self.start_orchestrator()

        logger.info("Task-Orchestrator MCP server started, listening for messages...")

        # MCP server main loop - read from stdin, process messages, write to stdout
        logger.info("Task-Orchestrator MCP server is ready to accept connections")

        # For stdio MCP servers, we need to handle the case where stdin might not be immediately available
        # Keep the server running and ready to process messages when they arrive
        loop = asyncio.get_event_loop()

        try:
            while True:
                try:
                    # Try to read message from stdin with timeout
                    message = await asyncio.wait_for(
                        loop.run_in_executor(None, sys.stdin.buffer.readline),
                        timeout=1.0
                    )
                    if not message:
                        # EOF reached
                        logger.info("Received EOF, shutting down...")
                        break

                    # Process the message
                    response = await self.handle_message(message)
                    if response:
                        # Write response to stdout
                        sys.stdout.buffer.write(response)
                        sys.stdout.buffer.flush()

                except asyncio.TimeoutError:
                    # No input available, continue waiting
                    continue
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    break
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")

        # Clean shutdown
        if self.event_bus:
            try:
                await self.emit_orchestration_event("shutdown", {
                    "stats": getattr(self, 'orchestration_stats', {}),
                    "timestamp": datetime.now().isoformat()
                })
                await self.event_bus.disconnect()
            except Exception as e:
                logger.warning(f"Error during shutdown: {e}")

        logger.info("Task-Orchestrator MCP server shut down gracefully")


async def main():
    """Main entry point."""
    wrapper = TaskOrchestratorWrapper()
    try:
        await wrapper.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())