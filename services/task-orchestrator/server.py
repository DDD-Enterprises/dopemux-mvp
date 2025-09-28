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

# Add dopemux to path for event bus integration
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
    from dopemux.producers.mcp_producer import MCPEventProducer
    EVENTS_ENABLED = True
except ImportError:
    EVENTS_ENABLED = False
    logging.warning("Event bus integration not available - continuing without events")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("task-orchestrator-wrapper")


class TaskOrchestratorWrapper:
    """
    MCP Wrapper for Task-Orchestrator with dependency analysis.

    This wrapper provides:
    - Transparent stdio proxy to the underlying task-orchestrator server
    - Event emission for dependency analysis and orchestration events
    - ADHD-friendly conflict detection and resolution guidance
    - Multi-instance coordination support
    """

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.event_bus: Optional[RedisStreamsAdapter] = None
        self.mcp_producer: Optional[MCPEventProducer] = None
        self.instance_id = os.getenv("DOPEMUX_INSTANCE", "default")
        self.workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

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
        """Start the underlying Task-Orchestrator server."""
        try:
            # Determine how to launch Task-Orchestrator
            # It's a Kotlin app, so might use gradle, java -jar, or a wrapper script
            orchestrator_path = os.getenv("TASK_ORCHESTRATOR_PATH",
                                         "/opt/task-orchestrator/bin/task-orchestrator")

            if os.path.exists(orchestrator_path):
                # Use the installed binary
                cmd = [orchestrator_path, "--mcp-mode"]
            elif os.getenv("USE_DOCKER", "false").lower() == "true":
                # Use Docker container
                cmd = [
                    "docker", "run", "-i", "--rm",
                    "--network", "mcp-network",
                    "task-orchestrator:latest"
                ]
            else:
                # Try to use gradle wrapper if in development
                gradle_wrapper = Path("/opt/task-orchestrator/gradlew")
                if gradle_wrapper.exists():
                    cmd = [str(gradle_wrapper), "run", "--args=--mcp-mode"]
                else:
                    # Fall back to trying Java directly
                    cmd = [
                        "java", "-jar",
                        "/opt/task-orchestrator/task-orchestrator.jar",
                        "--mcp-mode"
                    ]

            # Add any additional environment variables
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
            env["INSTANCE_ID"] = self.instance_id
            env["WORKSPACE_ID"] = self.workspace_id

            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=False  # Use binary mode for proper stdio handling
            )

            logger.info(f"Started Task-Orchestrator with command: {' '.join(cmd)}")

        except FileNotFoundError as e:
            logger.error(f"Failed to start Task-Orchestrator: {e}")
            logger.error("Please ensure Task-Orchestrator is installed")
            logger.error("Clone from: https://github.com/jpicklyk/task-orchestrator")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error starting Task-Orchestrator: {e}")
            sys.exit(1)

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
        Process a message from Claude Code, analyze for orchestration needs,
        and forward to the Task-Orchestrator server.
        """
        try:
            # Try to parse as JSON-RPC
            try:
                msg_str = message.decode('utf-8')
                msg_json = json.loads(msg_str)

                # Track method calls for orchestration analysis
                if msg_json.get("method") == "tools/call":
                    params = msg_json.get("params", {})
                    tool_name = params.get("name", "")

                    # Store pending call for response tracking
                    msg_id = msg_json.get("id")
                    if msg_id:
                        self.pending_calls[msg_id] = {
                            "tool": tool_name,
                            "params": params,
                            "start_time": datetime.now()
                        }

                    # Handle orchestration-specific tools
                    if tool_name in self._get_orchestration_tools():
                        await self._handle_orchestration_tool(tool_name, params)

                    # Show ADHD-friendly guidance if enabled
                    if self.adhd_config["dependency_visualization"]:
                        guidance = self._generate_orchestration_guidance(tool_name, params)
                        if guidance:
                            sys.stderr.write(f"\n{guidance}\n")
                            sys.stderr.flush()

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, just pass through
                pass

            # Forward to Task-Orchestrator
            if self.process and self.process.stdin:
                self.process.stdin.write(message)
                self.process.stdin.flush()

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_response(self, response: bytes) -> Optional[bytes]:
        """
        Process a response from Task-Orchestrator, analyze results,
        and forward to Claude Code.
        """
        try:
            # Try to parse as JSON-RPC response
            try:
                resp_str = response.decode('utf-8')
                resp_json = json.loads(resp_str)

                # Check if this is a response to a tracked call
                msg_id = resp_json.get("id")
                if msg_id and msg_id in self.pending_calls:
                    call_info = self.pending_calls.pop(msg_id)
                    duration = (datetime.now() - call_info["start_time"]).total_seconds()

                    # Process orchestration results
                    if "result" in resp_json:
                        await self._process_orchestration_result(
                            call_info["tool"],
                            resp_json["result"],
                            duration
                        )

                    # Update statistics
                    self.orchestration_stats["tasks_orchestrated"] += 1

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, just pass through
                pass

            # Forward to Claude Code
            sys.stdout.buffer.write(response)
            sys.stdout.buffer.flush()

        except Exception as e:
            logger.error(f"Error handling response: {e}")

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
        """Main run loop for the wrapper."""
        # Initialize event bus
        await self.initialize_event_bus()

        # Start Task-Orchestrator server
        await self.start_orchestrator()

        # Create tasks for reading from stdin and Task-Orchestrator
        tasks = []

        # Task to read from stdin and forward to Task-Orchestrator
        async def read_stdin():
            loop = asyncio.get_event_loop()
            while True:
                try:
                    # Read from stdin in non-blocking mode
                    message = await loop.run_in_executor(None, sys.stdin.buffer.read1, 8192)
                    if message:
                        await self.handle_message(message)
                    else:
                        # EOF reached
                        break
                except Exception as e:
                    logger.error(f"Error reading stdin: {e}")
                    break

        # Task to read from Task-Orchestrator and forward to stdout
        async def read_orchestrator():
            loop = asyncio.get_event_loop()
            while self.process and self.process.stdout:
                try:
                    # Read from Task-Orchestrator in non-blocking mode
                    response = await loop.run_in_executor(None, self.process.stdout.read1, 8192)
                    if response:
                        await self.handle_response(response)
                    else:
                        # EOF reached
                        break
                except Exception as e:
                    logger.error(f"Error reading from Task-Orchestrator: {e}")
                    break

        # Start both tasks
        tasks.append(asyncio.create_task(read_stdin()))
        tasks.append(asyncio.create_task(read_orchestrator()))

        # Also forward stderr
        async def read_stderr():
            loop = asyncio.get_event_loop()
            while self.process and self.process.stderr:
                try:
                    error = await loop.run_in_executor(None, self.process.stderr.read1, 8192)
                    if error:
                        sys.stderr.buffer.write(error)
                        sys.stderr.buffer.flush()
                    else:
                        break
                except Exception as e:
                    logger.error(f"Error reading stderr: {e}")
                    break

        tasks.append(asyncio.create_task(read_stderr()))

        # Wait for any task to complete (usually stdin EOF)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

        # Clean up
        if self.process:
            self.process.terminate()
            await asyncio.sleep(0.5)
            if self.process.poll() is None:
                self.process.kill()

        if self.event_bus:
            # Emit final statistics
            await self.emit_orchestration_event("shutdown", {
                "stats": self.orchestration_stats,
                "timestamp": datetime.now().isoformat()
            })
            await self.event_bus.disconnect()

        logger.info(f"Task-Orchestrator wrapper shut down. Stats: {self.orchestration_stats}")


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