"""
Shared console utilities for Dopemux.

Provides a pre-configured Rich console with .logger adapter for consistent
logging across all modules.
"""

from rich.console import Console


class _ConsoleAdapter:
    """Adapter that makes console.logger.info() work like console.print()."""

    def __init__(self, console: Console):
        self._console = console

    def info(self, *args, **kwargs):
        """Log info message using console.print()."""
        self._console.print(*args, **kwargs)

    def error(self, *args, **kwargs):
        """Log error message using console.print()."""
        self._console.print(*args, **kwargs)

    def warning(self, *args, **kwargs):
        """Log warning message using console.print()."""
        self._console.print(*args, **kwargs)


# Create and configure console
console = Console()
console.logger = _ConsoleAdapter(console)


__all__ = ['console']
