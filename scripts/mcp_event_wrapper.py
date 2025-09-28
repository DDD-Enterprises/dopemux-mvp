#!/usr/bin/env python3
"""
MCP Event Wrapper

This script wraps an MCP server with event emission capabilities.
It acts as a transparent proxy between Claude Code and the MCP server,
emitting events for all tool calls while passing through the protocol.

Usage:
    python mcp_event_wrapper.py --server conport --instance A
"""

import asyncio
import json
import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import Optional

# Add dopemux to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
from dopemux.producers.mcp_producer import MCPEventProducer
from dopemux.producers.conport_producer import ConPortEventProducer


class MCPEventWrapper:
    """
    Transparent event wrapper for MCP servers.

    This wrapper intercepts JSON-RPC messages between Claude Code
    and an MCP server, emitting events while passing through all
    communications unchanged.
    """

    def __init__(self, server_name: str, instance_id: str = "A"):
        self.server_name = server_name
        self.instance_id = instance_id

        # Event infrastructure
        self.event_bus: Optional[RedisStreamsAdapter] = None
        self.mcp_producer: Optional[MCPEventProducer] = None
        self.conport_producer: Optional[ConPortEventProducer] = None

        # Server process
        self.process: Optional[subprocess.Popen] = None

        # Message tracking
        self.pending_calls = {}
        self.start_times = {}

        # Server configurations
        self.server_configs = {
            "conport": {
                "command": [
                    "/Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp",
                    "--mode", "stdio",
                    "--workspace_id", "/Users/hue/code/dopemux-mvp"
                ],
                "env": {}
            },
            "context7": {
                "command": ["npx", "context7-mcp"],
                "env": {"CONTEXT7_API_KEY": os.environ.get("CONTEXT7_API_KEY", "")}
            },
            "zen": {
                "command": [
                    "python",
                    "/Users/hue/code/dopemux-mvp/services/zen/zen_mcp.py"
                ],
                "env": {
                    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                    "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "")
                }
            },
            "serena": {
                "command": [
                    "python",
                    "/Users/hue/code/dopemux-mvp/services/serena/server.py"
                ],
                "env": {
                    "WORKSPACE_ID": "/Users/hue/code/dopemux-mvp",
                    "MAX_SEARCH_RESULTS": "10",
                    "CONTEXT_DEPTH": "3",
                    "PROGRESSIVE_DISCLOSURE": "true",
                    "NAVIGATION_BREADCRUMBS": "true",
                    "INTELLIGENT_SUGGESTIONS": "true",
                    "GENTLE_GUIDANCE": "true",
                    "USE_UVX": "true",
                    "ADHD_MODE": "true"
                }
            },
            "gptr-researcher": {
                "command": [
                    "python",
                    "/Users/hue/code/dopemux-mvp/services/gptr/server.py"
                ],
                "env": {
                    "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY", ""),
                    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "")
                }
            }
        }

    async def initialize_event_bus(self):
        """Initialize connection to Redis event bus."""
        try:
            self.event_bus = RedisStreamsAdapter("redis://localhost:6379")
            await self.event_bus.connect()

            # Initialize producers
            self.mcp_producer = MCPEventProducer(self.event_bus, self.instance_id)

            if self.server_name == "conport":
                self.conport_producer = ConPortEventProducer(
                    self.event_bus, self.instance_id,
                    "/Users/hue/code/dopemux-mvp"
                )

            # Log wrapper start
            sys.stderr.write(f"[EVENT_WRAPPER] Connected to event bus for {self.server_name}\n")
            sys.stderr.flush()

        except Exception as e:
            # Event bus failure should not prevent MCP from working
            sys.stderr.write(f"[EVENT_WRAPPER] Failed to connect to event bus: {e}\n")
            sys.stderr.write("[EVENT_WRAPPER] Continuing without event emission\n")
            sys.stderr.flush()

    async def start_server(self):
        """Start the underlying MCP server process."""
        if self.server_name not in self.server_configs:
            raise ValueError(f"Unknown server: {self.server_name}")

        config = self.server_configs[self.server_name]

        # Merge environments
        env = os.environ.copy()
        env.update(config["env"])

        # Start subprocess
        self.process = subprocess.Popen(
            config["command"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=False  # Use binary mode for proper handling
        )

        sys.stderr.write(f"[EVENT_WRAPPER] Started {self.server_name} MCP server\n")
        sys.stderr.flush()

    async def process_stdin_to_server(self, writer):
        """Process messages from Claude Code to MCP server."""
        loop = asyncio.get_event_loop()

        while True:
            try:
                # Read from stdin (Claude Code)
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                # Parse and track if JSON-RPC
                try:
                    message = json.loads(line)
                    await self.handle_request(message)
                except json.JSONDecodeError:
                    pass

                # Forward to server
                self.process.stdin.write(line.encode() if isinstance(line, str) else line)
                self.process.stdin.flush()

            except Exception as e:
                sys.stderr.write(f"[EVENT_WRAPPER] Error in stdin processing: {e}\n")
                sys.stderr.flush()

    async def process_server_to_stdout(self, reader):
        """Process messages from MCP server to Claude Code."""
        while True:
            try:
                # Read from server
                line = self.process.stdout.readline()
                if not line:
                    break

                # Parse and track if JSON-RPC
                try:
                    message = json.loads(line)
                    await self.handle_response(message)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

                # Forward to Claude Code
                sys.stdout.write(line.decode() if isinstance(line, bytes) else line)
                sys.stdout.flush()

            except Exception as e:
                sys.stderr.write(f"[EVENT_WRAPPER] Error in stdout processing: {e}\n")
                sys.stderr.flush()

    async def process_server_stderr(self):
        """Forward server stderr to Claude Code stderr."""
        while True:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break

                sys.stderr.write(line.decode() if isinstance(line, bytes) else line)
                sys.stderr.flush()

            except Exception as e:
                sys.stderr.write(f"[EVENT_WRAPPER] Error in stderr processing: {e}\n")
                sys.stderr.flush()

    async def handle_request(self, message: dict):
        """Handle request from Claude Code to MCP server."""
        if not self.mcp_producer:
            return

        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        if method and msg_id:
            # Track call
            import time
            self.start_times[msg_id] = time.time()
            self.pending_calls[msg_id] = {
                "method": method,
                "params": params
            }

            # Emit start event
            tool_name = f"mcp__{self.server_name}__{method}"
            try:
                await self.mcp_producer.on_tool_call_start(tool_name, params)
            except Exception as e:
                sys.stderr.write(f"[EVENT_WRAPPER] Error emitting start event: {e}\n")
                sys.stderr.flush()

    async def handle_response(self, message: dict):
        """Handle response from MCP server to Claude Code."""
        if not self.mcp_producer:
            return

        msg_id = message.get("id")

        if msg_id and msg_id in self.pending_calls:
            import time
            duration_ms = int((time.time() - self.start_times.pop(msg_id, 0)) * 1000)
            call_info = self.pending_calls.pop(msg_id)

            # Extract result or error
            result = message.get("result")
            error = message.get("error")

            # Emit completion event
            tool_name = f"mcp__{self.server_name}__{call_info['method']}"
            try:
                await self.mcp_producer.on_tool_call_complete(
                    msg_id,
                    tool_name,
                    call_info["params"],
                    result,
                    str(error) if error else None
                )

                # Emit ConPort-specific events
                if self.conport_producer and self.server_name == "conport" and not error:
                    await self.emit_conport_event(
                        call_info["method"],
                        call_info["params"],
                        result
                    )

            except Exception as e:
                sys.stderr.write(f"[EVENT_WRAPPER] Error emitting completion event: {e}\n")
                sys.stderr.flush()

    async def emit_conport_event(self, method: str, params: dict, result: any):
        """Emit ConPort-specific domain events."""
        try:
            if method == "log_decision" and isinstance(result, dict):
                await self.conport_producer.on_decision_logged(
                    decision_id=result.get("id", 0),
                    summary=params.get("summary", ""),
                    rationale=params.get("rationale", ""),
                    tags=params.get("tags", []),
                    implementation_details=params.get("implementation_details")
                )

            elif method == "log_progress" and isinstance(result, dict):
                await self.conport_producer.on_progress_updated(
                    progress_id=result.get("id", 0),
                    description=params.get("description", ""),
                    old_status="pending",
                    new_status=params.get("status", "active")
                )

            elif method == "get_active_context":
                await self.conport_producer.on_context_accessed(
                    context_type="active_context",
                    access_reason="mcp_call"
                )

        except Exception as e:
            sys.stderr.write(f"[EVENT_WRAPPER] Error emitting ConPort event: {e}\n")
            sys.stderr.flush()

    async def run(self):
        """Run the event wrapper."""
        # Initialize event bus (non-blocking if Redis unavailable)
        await self.initialize_event_bus()

        # Start the MCP server
        await self.start_server()

        # Create tasks for bidirectional communication
        tasks = [
            asyncio.create_task(self.process_stdin_to_server(None)),
            asyncio.create_task(self.process_server_to_stdout(None)),
            asyncio.create_task(self.process_server_stderr())
        ]

        try:
            # Run until interrupted
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            sys.stderr.write("[EVENT_WRAPPER] Shutting down...\n")
            sys.stderr.flush()
        finally:
            # Cleanup
            if self.process:
                self.process.terminate()
                self.process.wait()

            if self.event_bus:
                await self.event_bus.disconnect()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Event Wrapper")
    parser.add_argument(
        "--server",
        required=True,
        choices=["conport", "context7", "zen", "task-master-ai", "gptr-researcher"],
        help="MCP server to wrap"
    )
    parser.add_argument(
        "--instance",
        default=os.environ.get("DOPEMUX_INSTANCE_ID", "A"),
        help="Instance ID for event namespacing"
    )

    args = parser.parse_args()

    # Create and run wrapper
    wrapper = MCPEventWrapper(args.server, args.instance)
    asyncio.run(wrapper.run())


if __name__ == "__main__":
    main()