"""
Lightweight FastMCP stub for test environments without fastmcp installed.

Provides minimal decorators so module import succeeds during unit tests.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class FastMCP:
    """Fallback implementation that no-ops tool registration."""

    def __init__(self, name: str):
        self.name = name

    def tool(self, *dargs: Any, **dkwargs: Any) -> Callable:
        """Decorator that returns the original function unchanged."""

        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    def custom_route(self, *dargs: Any, **dkwargs: Any) -> Callable:
        """Decorator stub for custom routes."""

        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    def run(self, *args: Any, **kwargs: Any):
        """Stub run method that logs a warning."""
        logger.warning(
            "fastmcp not installed; FastMCP.run() stub invoked. "
            "Install fastmcp for full MCP functionality."
        )
