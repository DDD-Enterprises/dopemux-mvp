"""
Claude Code MCP Server Management

Constrained Dynamic Loading for MCP servers used by Claude Code.
Provides intelligent server activation with safety controls and token optimization.
"""

from .loader import ConstrainedDynamicLoader, LoaderConfig

__version__ = "1.0.0"

__all__ = [
    "ConstrainedDynamicLoader",
    "LoaderConfig"
]