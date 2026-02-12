#!/usr/bin/env python3
"""
MCP Capture Server - Expose emit_capture_event() as MCP tool.

Implements CLI-INT-002: Cross-adapter capture integration.
Enables MCP-based adapters (Codex, future tools) to emit events
to Chronicle with content-addressed deduplication.

Tool: capture/emit
- Wraps emit_capture_event() from dopemux.memory.capture_client
- Returns structured CaptureResult
- Enforces lane policy and audit logging
- Supports all capture modes (plugin, cli, mcp, auto)
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Add dopemux to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from dopemux.memory.capture_client import (
    emit_capture_event,
    CaptureResult,
    CaptureError,
)

# Configure logging to stderr (MCP uses stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-capture")


class CaptureMCPServer:
    """MCP server exposing Chronicle capture as a tool."""

    def __init__(self):
        self.server = Server("dopemux-capture")
        self._setup_tools()

    def _setup_tools(self):
        """Register MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="capture/emit",
                    description=(
                        "Emit an event to Chronicle database with content-addressed deduplication. "
                        "Enforces lane-based capture policy and audit logging. "
                        "Returns event_id and insertion status."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event": {
                                "type": "object",
                                "description": "Event envelope with event_type, ts_utc, session_id, source, payload",
                                "required": ["event_type"],
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["plugin", "cli", "mcp", "auto"],
                                "default": "mcp",
                                "description": "Capture mode (defaults to mcp for MCP adapters)",
                            },
                            "lane": {
                                "type": "string",
                                "description": "Lane identifier for policy enforcement (e.g., 'agent:primary')",
                            },
                            "repo_root": {
                                "type": "string",
                                "description": "Repository root path (auto-detected if not provided)",
                            },
                        },
                        "required": ["event"],
                    },
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if name != "capture/emit":
                raise ValueError(f"Unknown tool: {name}")

            try:
                # Extract parameters
                event = arguments["event"]
                mode = arguments.get("mode", "mcp")
                lane = arguments.get("lane")
                repo_root_str = arguments.get("repo_root")

                repo_root = Path(repo_root_str) if repo_root_str else None

                # Call emit_capture_event
                result: CaptureResult = emit_capture_event(
                    event,
                    mode=mode,
                    repo_root=repo_root,
                    lane=lane,
                )

                # Build response
                response = {
                    "success": True,
                    "event_id": result.event_id,
                    "inserted": result.inserted,
                    "ledger_path": str(result.ledger_path),
                    "repo_root": str(result.repo_root),
                    "mode": result.mode,
                    "source": result.source,
                    "event_type": result.event_type,
                }

                logger.info(
                    f"Captured event: {result.event_type} → {result.event_id[:8]}... (inserted={result.inserted})"
                )

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except CaptureError as e:
                logger.error(f"Capture error: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"success": False, "error": str(e)}, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"success": False, "error": f"Internal error: {e}"},
                            indent=2,
                        ),
                    )
                ]

    async def run(self):
        """Run the MCP server via stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """Main entry point."""
    logger.info("Starting MCP Capture Server")
    server = CaptureMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
