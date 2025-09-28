"""
Event producers for Dopemux services.

Automatically emit events when key actions occur in MCP, ConPort, and other services.
"""

from .mcp_producer import MCPEventProducer
from .conport_producer import ConPortEventProducer

__all__ = ["MCPEventProducer", "ConPortEventProducer"]