"""
MCP Protocol Event Wrapper

Wraps Model Context Protocol communications with event emission.
This integrates at the protocol level for stdio and TCP-based MCP servers.
"""

import asyncio
import json
import time
import sys
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import subprocess
from asyncio.subprocess import Process

from .event_bus import EventBus, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
from .producers.mcp_producer import MCPEventProducer
from .producers.conport_producer import ConPortEventProducer


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    stdio: bool = True  # True for stdio, False for TCP
    host: Optional[str] = None
    port: Optional[int] = None
    instance_id: str = "default"


class MCPProtocolEventWrapper:
    """
    Wraps MCP protocol communications with event emission.

    This wrapper sits between Claude Code and MCP servers,
    intercepting JSON-RPC messages and emitting events while
    transparently passing through the actual protocol messages.
    """

    def __init__(self,
                 server_config: MCPServerConfig,
                 event_bus: EventBus,
                 instance_id: str = "default"):
        self.config = server_config
        self.event_bus = event_bus
        self.instance_id = instance_id

        # Event producers
        self.mcp_producer = MCPEventProducer(event_bus, instance_id)
        self.conport_producer = None
        if server_config.name == "conport":
            self.conport_producer = ConPortEventProducer(
                event_bus, instance_id, "/Users/hue/code/dopemux-mvp"
            )

        # Process management
        self.process: Optional[Process] = None
        self.reader_task: Optional[asyncio.Task] = None
        self.writer_task: Optional[asyncio.Task] = None

        # Message tracking
        self.pending_calls: Dict[str, Dict[str, Any]] = {}
        self.call_metrics: Dict[str, List[float]] = {}

    async def start(self):
        """Start the MCP server process with event wrapper."""
        if self.config.stdio:
            await self._start_stdio_server()
        else:
            await self._start_tcp_server()

        print(f"🔗 MCP Protocol Wrapper started for {self.config.name} (instance {self.instance_id})")

    async def stop(self):
        """Stop the wrapped MCP server."""
        if self.reader_task:
            self.reader_task.cancel()
        if self.writer_task:
            self.writer_task.cancel()

        if self.process:
            self.process.terminate()
            await self.process.wait()

        print(f"🔗 MCP Protocol Wrapper stopped for {self.config.name}")

    async def _start_stdio_server(self):
        """Start an stdio-based MCP server with wrapper."""
        # Create subprocess with pipes
        self.process = await asyncio.create_subprocess_exec(
            *self.config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **self.config.env}
        )

        # Start reader and writer tasks
        self.reader_task = asyncio.create_task(
            self._read_from_server(self.process.stdout)
        )
        self.writer_task = asyncio.create_task(
            self._write_to_server(self.process.stdin)
        )

    async def _start_tcp_server(self):
        """Start a TCP-based MCP server connection with wrapper."""
        # Connect to TCP server
        reader, writer = await asyncio.open_connection(
            self.config.host, self.config.port
        )

        # Start reader and writer tasks
        self.reader_task = asyncio.create_task(
            self._read_from_tcp(reader)
        )
        self.writer_task = asyncio.create_task(
            self._write_to_tcp(writer)
        )

    async def _read_from_server(self, stdout):
        """Read messages from MCP server stdout and emit events."""
        while True:
            try:
                line = await stdout.readline()
                if not line:
                    break

                # Parse JSON-RPC message
                try:
                    message = json.loads(line.decode())
                    await self._process_server_message(message)

                    # Forward to Claude Code
                    sys.stdout.write(line.decode())
                    sys.stdout.flush()

                except json.JSONDecodeError:
                    # Not JSON, just forward
                    sys.stdout.write(line.decode())
                    sys.stdout.flush()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error reading from server: {e}", file=sys.stderr)

    async def _write_to_server(self, stdin):
        """Write messages from Claude Code to MCP server and emit events."""
        while True:
            try:
                # Read from Claude Code stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                # Parse JSON-RPC message
                try:
                    message = json.loads(line)
                    await self._process_client_message(message)

                except json.JSONDecodeError:
                    pass

                # Forward to server
                stdin.write(line.encode())
                await stdin.drain()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error writing to server: {e}", file=sys.stderr)

    async def _process_client_message(self, message: Dict[str, Any]):
        """Process message from Claude Code to server."""
        if "method" in message:
            # This is a method call
            method = message["method"]
            params = message.get("params", {})
            msg_id = message.get("id")

            if msg_id:
                # Track pending call
                start_time = time.time()
                self.pending_calls[msg_id] = {
                    "method": method,
                    "params": params,
                    "start_time": start_time
                }

                # Emit tool call start event
                tool_name = f"mcp__{self.config.name}__{method}"
                await self.mcp_producer.on_tool_call_start(tool_name, params)

                # Emit ConPort-specific events if applicable
                if self.conport_producer and method.startswith("conport__"):
                    await self._emit_conport_request_event(method, params)

    async def _process_server_message(self, message: Dict[str, Any]):
        """Process message from server to Claude Code."""
        msg_id = message.get("id")

        if msg_id and msg_id in self.pending_calls:
            # This is a response to a tracked call
            call_info = self.pending_calls.pop(msg_id)
            duration_ms = int((time.time() - call_info["start_time"]) * 1000)

            # Extract result or error
            result = message.get("result")
            error = message.get("error")

            # Emit tool call complete event
            tool_name = f"mcp__{self.config.name}__{call_info['method']}"
            await self.mcp_producer.on_tool_call_complete(
                msg_id,
                tool_name,
                call_info["params"],
                result,
                str(error) if error else None
            )

            # Track metrics
            if tool_name not in self.call_metrics:
                self.call_metrics[tool_name] = []
            self.call_metrics[tool_name].append(duration_ms)

            # Emit ConPort-specific events if applicable
            if self.conport_producer and not error:
                await self._emit_conport_response_event(
                    call_info["method"], call_info["params"], result
                )

    async def _emit_conport_request_event(self, method: str, params: Dict[str, Any]):
        """Emit ConPort-specific request events."""
        # Clean method name
        method = method.replace("conport__", "")

        if method == "get_active_context":
            await self.conport_producer.on_context_accessed(
                context_type="active_context",
                access_reason="mcp_protocol_call"
            )

    async def _emit_conport_response_event(self, method: str, params: Dict[str, Any], result: Any):
        """Emit ConPort-specific response events."""
        # Clean method name
        method = method.replace("conport__", "")

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

        elif method == "log_custom_data" and isinstance(result, dict):
            await self.conport_producer.on_custom_data_logged(
                category=params.get("category", ""),
                key=params.get("key", ""),
                value=params.get("value"),
                operation="create"
            )

    async def emit_performance_metrics(self):
        """Emit aggregated performance metrics."""
        for tool_name, durations in self.call_metrics.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)

                event = DopemuxEvent.create(
                    event_type="mcp.performance.metrics",
                    namespace=f"instance.{self.instance_id}.metrics",
                    payload={
                        "tool": tool_name,
                        "server": self.config.name,
                        "call_count": len(durations),
                        "avg_duration_ms": avg_duration,
                        "max_duration_ms": max_duration,
                        "min_duration_ms": min_duration,
                        "timestamp": datetime.now().isoformat()
                    },
                    source="mcp.protocol.wrapper",
                    priority=Priority.LOW,
                    adhd_metadata=ADHDMetadata(
                        cognitive_load=CognitiveLoad.MINIMAL,
                        attention_required=False,
                        interruption_safe=True,
                        focus_context="performance_monitoring",
                        batching_allowed=True
                    )
                )

                await self.event_bus.publish(event)


class MCPProtocolOrchestrator:
    """
    Orchestrates multiple MCP servers with event wrappers.

    This manages the lifecycle of wrapped MCP servers and
    provides coordination between them through events.
    """

    def __init__(self, event_bus: EventBus, instance_id: str = "default"):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.wrappers: Dict[str, MCPProtocolEventWrapper] = {}

    def register_server(self, config: MCPServerConfig):
        """Register an MCP server for wrapped execution."""
        wrapper = MCPProtocolEventWrapper(config, self.event_bus, self.instance_id)
        self.wrappers[config.name] = wrapper

    async def start_all(self):
        """Start all registered MCP servers with wrappers."""
        print(f"🚀 Starting MCP Protocol Orchestrator for instance {self.instance_id}")

        for name, wrapper in self.wrappers.items():
            try:
                await wrapper.start()
                print(f"   ✅ Started {name}")
            except Exception as e:
                print(f"   ❌ Failed to start {name}: {e}")

    async def stop_all(self):
        """Stop all wrapped MCP servers."""
        print(f"🛑 Stopping MCP Protocol Orchestrator")

        for name, wrapper in self.wrappers.items():
            try:
                await wrapper.stop()
                print(f"   ✅ Stopped {name}")
            except Exception as e:
                print(f"   ❌ Failed to stop {name}: {e}")

    async def emit_orchestration_event(self, event_type: str, payload: Dict[str, Any]):
        """Emit orchestration-level events."""
        event = DopemuxEvent.create(
            event_type=f"mcp.orchestration.{event_type}",
            namespace=f"instance.{self.instance_id}.orchestration",
            payload={
                **payload,
                "instance_id": self.instance_id,
                "servers": list(self.wrappers.keys()),
                "timestamp": datetime.now().isoformat()
            },
            source="mcp.orchestrator",
            priority=Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW,
                attention_required=False,
                interruption_safe=True,
                focus_context="system_orchestration"
            )
        )

        await self.event_bus.publish(event)

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all wrapped servers."""
        health = {}
        for name, wrapper in self.wrappers.items():
            if wrapper.process:
                health[name] = wrapper.process.returncode is None
            else:
                health[name] = False

        return health


import os  # Add this import at the top


def create_claude_code_wrapper():
    """
    Create a wrapper configuration for Claude Code MCP integration.

    This function sets up the event wrapper that will intercept
    all MCP communications from Claude Code.
    """
    from .event_bus import RedisStreamsAdapter

    # Initialize event bus
    event_bus = RedisStreamsAdapter("redis://localhost:6379")

    # Get instance ID from environment or use default
    instance_id = os.environ.get("DOPEMUX_INSTANCE_ID", "default")

    # Create orchestrator
    orchestrator = MCPProtocolOrchestrator(event_bus, instance_id)

    # Register critical MCP servers
    orchestrator.register_server(MCPServerConfig(
        name="conport",
        command=["python", "/app/conport_mcp.py"],
        env={"WORKSPACE_ID": "/Users/hue/code/dopemux-mvp"},
        stdio=True,
        instance_id=instance_id
    ))

    orchestrator.register_server(MCPServerConfig(
        name="context7",
        command=["node", "/app/context7_server.js"],
        env={"CONTEXT7_API_KEY": os.environ.get("CONTEXT7_API_KEY", "")},
        stdio=True,
        instance_id=instance_id
    ))

    orchestrator.register_server(MCPServerConfig(
        name="zen",
        command=["python", "/app/zen_mcp.py"],
        env={
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
            "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "")
        },
        stdio=True,
        instance_id=instance_id
    ))

    return orchestrator