#!/usr/bin/env python3
"""
Serena v2 MCP Server
Exposes 31-component ADHD-optimized code intelligence via MCP protocol

Phase 1: Basic MCP skeleton with 2 simple tools
Phase 2: Integration with Serena v2 intelligence system
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, EmptyResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("serena-v2-mcp")


class SerenaV2MCPServer:
    """
    MCP Server wrapper for Serena v2 intelligence system

    Phase 1: Basic file operations (read_file, list_dir)
    Phase 2: Serena integration (find_symbol, search_for_pattern)
    """

    def __init__(self):
        self.server = Server("serena-v2")
        self.workspace: Optional[Path] = None
        self.serena_system: Optional[Dict[str, Any]] = None

        logger.info("Serena v2 MCP Server initialized")

    async def initialize(self):
        """Initialize workspace and Serena v2 system"""
        # Phase 1: Basic workspace detection
        # TODO Phase 2: Use SerenaAutoActivator for intelligent detection

        self.workspace = self._detect_workspace()

        if self.workspace:
            logger.info(f"✓ Workspace detected: {self.workspace}")
        else:
            logger.warning("⚠ No workspace detected - will use current directory")
            self.workspace = Path.cwd()

        # TODO Phase 2: Initialize Serena v2 (31 components)
        # self.serena_system = await setup_complete_cognitive_load_management_system(
        #     workspace_id=str(self.workspace)
        # )

    def _detect_workspace(self) -> Optional[Path]:
        """
        Simple workspace detection (looks for .git)

        Phase 2 will use SerenaAutoActivator for advanced detection
        """
        current = Path.cwd()

        # Walk up looking for .git
        for _ in range(10):
            if (current / '.git').exists():
                return current

            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Safely resolve relative path against workspace

        Args:
            relative_path: Path relative to workspace root

        Returns:
            Absolute path

        Raises:
            ValueError: If path is outside workspace
        """
        if not self.workspace:
            raise ValueError("No workspace initialized")

        full_path = (self.workspace / relative_path).resolve()

        # Security: Ensure path is within workspace
        try:
            full_path.relative_to(self.workspace)
        except ValueError:
            raise ValueError(
                f"❌ Security: Path '{relative_path}' is outside workspace\n"
                f"   Workspace: {self.workspace}\n"
                f"   Attempted: {full_path}"
            )

        return full_path

    def register_tools(self):
        """Register MCP tools with the server"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="read_file",
                    description="Reads a file from the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "Path relative to workspace root"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "First line to read (0-indexed, optional)",
                                "default": 0
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "Last line to read (optional, null = end of file)"
                            }
                        },
                        "required": ["relative_path"]
                    }
                ),
                Tool(
                    name="list_dir",
                    description="Lists files and directories in a given path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "Directory path relative to workspace"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Whether to list recursively",
                                "default": False
                            }
                        },
                        "required": ["relative_path"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Route tool calls to implementations"""
            try:
                if name == "read_file":
                    result = await self.read_file_tool(**arguments)
                elif name == "list_dir":
                    result = await self.list_dir_tool(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"❌ Error in {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=error_msg)]

    async def read_file_tool(
        self,
        relative_path: str,
        start_line: int = 0,
        end_line: Optional[int] = None
    ) -> str:
        """
        Read file with optional line range

        Returns content in cat -n format with line numbers
        """
        file_path = self._resolve_path(relative_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ File not found: {relative_path}\n"
                f"   Workspace: {self.workspace}\n"
                f"   Looking for: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"❌ Not a file: {relative_path}\n"
                f"   Path is a directory, use list_dir instead"
            )

        # Read file
        content = file_path.read_text()
        lines = content.splitlines()

        # Apply line range
        if end_line is None:
            selected_lines = lines[start_line:]
        else:
            selected_lines = lines[start_line:end_line + 1]

        # Format with line numbers (cat -n style)
        numbered_lines = []
        for i, line in enumerate(selected_lines):
            line_num = start_line + i + 1
            numbered_lines.append(f"{line_num:6d}→{line}")

        result = "\n".join(numbered_lines)

        logger.info(f"read_file: {relative_path} ({len(selected_lines)} lines)")
        return result

    async def list_dir_tool(
        self,
        relative_path: str,
        recursive: bool = False
    ) -> str:
        """
        List directory contents

        Returns JSON structure with directories and files
        """
        dir_path = self._resolve_path(relative_path)

        if not dir_path.exists():
            raise FileNotFoundError(
                f"❌ Directory not found: {relative_path}\n"
                f"   Workspace: {self.workspace}\n"
                f"   Looking for: {dir_path}"
            )

        if not dir_path.is_dir():
            raise ValueError(
                f"❌ Not a directory: {relative_path}\n"
                f"   Path is a file, use read_file instead"
            )

        # List directory
        result = {"directories": [], "files": []}

        if recursive:
            # Recursive listing
            for item in dir_path.rglob('*'):
                # Skip .git and common ignore patterns
                if '.git' in item.parts or '__pycache__' in item.parts:
                    continue

                rel_path = str(item.relative_to(dir_path))
                if item.is_dir():
                    result["directories"].append(rel_path)
                else:
                    result["files"].append(rel_path)
        else:
            # Non-recursive listing
            for item in dir_path.iterdir():
                # Skip hidden files starting with .
                if item.name.startswith('.'):
                    continue

                if item.is_dir():
                    result["directories"].append(item.name)
                else:
                    result["files"].append(item.name)

        # Sort for consistent output
        result["directories"].sort()
        result["files"].sort()

        # Format as readable text
        output_lines = []

        if result["directories"]:
            output_lines.append("Directories:")
            for d in result["directories"]:
                output_lines.append(f"  {d}/")

        if result["files"]:
            if result["directories"]:
                output_lines.append("")
            output_lines.append("Files:")
            for f in result["files"]:
                output_lines.append(f"  {f}")

        if not result["directories"] and not result["files"]:
            output_lines.append("(empty directory)")

        logger.info(f"list_dir: {relative_path} ({len(result['directories'])} dirs, {len(result['files'])} files)")
        return "\n".join(output_lines)


async def main():
    """Main entry point for Serena v2 MCP server"""
    logger.info("="*60)
    logger.info("SERENA V2 MCP SERVER")
    logger.info("Phase 1: Basic MCP skeleton")
    logger.info("="*60)

    # Create server instance
    server_instance = SerenaV2MCPServer()

    # Initialize workspace
    await server_instance.initialize()

    # Register tools
    server_instance.register_tools()

    logger.info("="*60)
    logger.info("Server ready - awaiting tool calls")
    logger.info(f"Workspace: {server_instance.workspace}")
    logger.info(f"Tools: read_file, list_dir")
    logger.info("="*60)

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
