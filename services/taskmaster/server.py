#!/usr/bin/env python3
"""
Task-Master-AI MCP Server Wrapper

This wrapper provides an MCP server interface for Task-Master-AI,
which handles PRD parsing and task decomposition with ADHD accommodations.

The wrapper can either:
1. Launch the external task-master-ai package via uvx
2. Act as a stdio proxy with event emission capabilities
"""

import asyncio
import json
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

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
logger = logging.getLogger("task-master-wrapper")


class TaskMasterWrapper:
    """
    MCP Wrapper for Task-Master-AI with ADHD accommodations.

    This wrapper provides:
    - Transparent stdio proxy to the underlying task-master-ai server
    - Event emission for task creation and updates
    - ADHD-friendly progress tracking
    - ConPort integration for decision tracking
    """

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.event_bus: Optional[RedisStreamsAdapter] = None
        self.mcp_producer: Optional[MCPEventProducer] = None
        self.instance_id = os.getenv("DOPEMUX_INSTANCE", "default")
        self.workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

        # ADHD configuration
        self.adhd_config = {
            "task_chunk_size": int(os.getenv("TASK_CHUNK_SIZE", "5")),  # Max tasks per chunk
            "focus_duration": int(os.getenv("FOCUS_DURATION", "25")),   # Minutes per session
            "celebration_enabled": os.getenv("CELEBRATION_ENABLED", "true").lower() == "true",
            "progress_visualization": os.getenv("PROGRESS_VIZ", "true").lower() == "true"
        }

        # Track active tasks for progress monitoring
        self.active_tasks = {}
        self.pending_calls = {}

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

    async def start_task_master(self):
        """Start the underlying Task-Master-AI server."""
        try:
            # Check if we should use uvx or npx
            use_uvx = os.getenv("USE_UVX", "true").lower() == "true"

            if use_uvx:
                # Use uvx to run task-master-ai
                cmd = ["uvx", "task-master-ai"]
            else:
                # Use npx for the Node.js version
                cmd = ["npx", "claude-task-master"]

            # Add any additional environment variables
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
            env["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")

            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=False  # Use binary mode for proper stdio handling
            )

            logger.info(f"Started Task-Master-AI server with command: {' '.join(cmd)}")

        except FileNotFoundError as e:
            logger.error(f"Failed to start Task-Master-AI: {e}")
            logger.error("Please install task-master-ai via: uvx install task-master-ai")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error starting Task-Master-AI: {e}")
            sys.exit(1)

    async def emit_task_event(self, event_type: str, data: Dict[str, Any]):
        """Emit a task-related event to the event bus."""
        if not self.mcp_producer:
            return

        try:
            event = DopemuxEvent(
                event_type=f"task.{event_type}",
                source=f"task-master-{self.instance_id}",
                instance_id=self.instance_id,
                data=data,
                priority=Priority.MEDIUM,
                cognitive_load=CognitiveLoad.MEDIUM,
                adhd_metadata=ADHDMetadata(
                    interruption_allowed=event_type != "in_progress",
                    focus_required=event_type == "in_progress",
                    time_sensitive=False,
                    can_batch=True
                )
            )

            await self.event_bus.publish(event)
            logger.debug(f"Emitted {event_type} event for task")

        except Exception as e:
            logger.warning(f"Failed to emit event: {e}")

    async def handle_message(self, message: bytes) -> Optional[bytes]:
        """
        Process a message from Claude Code, optionally emit events,
        and forward to the Task-Master-AI server.
        """
        try:
            # Try to parse as JSON-RPC
            try:
                msg_str = message.decode('utf-8')
                msg_json = json.loads(msg_str)

                # Track method calls for event emission
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

                    # Emit event for task creation
                    if tool_name in ["create_task", "parse_prd", "decompose_task"]:
                        await self.emit_task_event("created", {
                            "tool": tool_name,
                            "params": params,
                            "timestamp": datetime.now().isoformat()
                        })

                        # Show ADHD-friendly progress if enabled
                        if self.adhd_config["progress_visualization"]:
                            progress_msg = self._generate_progress_message(tool_name)
                            if progress_msg:
                                sys.stderr.write(f"\n{progress_msg}\n")
                                sys.stderr.flush()

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, just pass through
                pass

            # Forward to Task-Master-AI
            if self.process and self.process.stdin:
                self.process.stdin.write(message)
                self.process.stdin.flush()

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_response(self, response: bytes) -> Optional[bytes]:
        """
        Process a response from Task-Master-AI, optionally emit events,
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

                    # Emit completion event
                    await self.emit_task_event("completed", {
                        "tool": call_info["tool"],
                        "duration": duration,
                        "success": "error" not in resp_json,
                        "timestamp": datetime.now().isoformat()
                    })

                    # Celebrate completion if enabled
                    if self.adhd_config["celebration_enabled"] and "error" not in resp_json:
                        celebration = self._generate_celebration(call_info["tool"])
                        if celebration:
                            sys.stderr.write(f"\n{celebration}\n")
                            sys.stderr.flush()

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, just pass through
                pass

            # Forward to Claude Code
            sys.stdout.buffer.write(response)
            sys.stdout.buffer.flush()

        except Exception as e:
            logger.error(f"Error handling response: {e}")

    def _generate_progress_message(self, tool_name: str) -> str:
        """Generate ADHD-friendly progress messages."""
        messages = {
            "create_task": "🎯 Creating new task...",
            "parse_prd": "📋 Parsing PRD document...",
            "decompose_task": "🔍 Breaking down into subtasks...",
            "update_task": "✏️ Updating task details...",
            "complete_task": "✅ Marking task complete..."
        }
        return messages.get(tool_name, f"⚡ Processing {tool_name}...")

    def _generate_celebration(self, tool_name: str) -> str:
        """Generate ADHD-friendly celebration messages."""
        celebrations = {
            "create_task": "✨ Task created successfully!",
            "parse_prd": "🎉 PRD parsed and understood!",
            "decompose_task": "🌟 Task breakdown complete!",
            "update_task": "💫 Task updated!",
            "complete_task": "🎊 Task completed - great work!"
        }
        return celebrations.get(tool_name, "✅ Operation successful!")

    async def run(self):
        """Main run loop for the wrapper."""
        # Initialize event bus
        await self.initialize_event_bus()

        # Start Task-Master-AI server
        await self.start_task_master()

        # Create tasks for reading from stdin and Task-Master-AI
        tasks = []

        # Task to read from stdin and forward to Task-Master-AI
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

        # Task to read from Task-Master-AI and forward to stdout
        async def read_task_master():
            loop = asyncio.get_event_loop()
            while self.process and self.process.stdout:
                try:
                    # Read from Task-Master-AI in non-blocking mode
                    response = await loop.run_in_executor(None, self.process.stdout.read1, 8192)
                    if response:
                        await self.handle_response(response)
                    else:
                        # EOF reached
                        break
                except Exception as e:
                    logger.error(f"Error reading from Task-Master-AI: {e}")
                    break

        # Start both tasks
        tasks.append(asyncio.create_task(read_stdin()))
        tasks.append(asyncio.create_task(read_task_master()))

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
            await self.event_bus.disconnect()

        logger.info("Task-Master-AI wrapper shut down")


async def main():
    """Main entry point."""
    wrapper = TaskMasterWrapper()
    try:
        await wrapper.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())