"""
MCP Capture Server

Exposes Chronicle capture pipeline as MCP tool for cross-adapter integration.

Tool:
    capture/emit - Emit events to Chronicle with content-addressed deduplication

See README.md for usage examples.
"""

__version__ = "1.0.0"
__all__ = ["CaptureMCPServer"]

from .server import CaptureMCPServer
