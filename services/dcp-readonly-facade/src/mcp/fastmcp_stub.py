"""Lightweight FastMCP stub for environments without fastmcp installed.

Provides minimal decorators so module import succeeds during unit tests and
byte-compilation. Mirrors the stub used by services/dope-context.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class FastMCP:
    """Fallback implementation that no-ops tool registration."""

    def __init__(self, name: str):
        self.name = name

    def tool(self, *dargs: Any, **dkwargs: Any) -> Callable:
        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    def run(self, *args: Any, **kwargs: Any) -> None:
        logger.warning(
            "fastmcp not installed; FastMCP.run() stub invoked. "
            "Install fastmcp for full MCP functionality."
        )
