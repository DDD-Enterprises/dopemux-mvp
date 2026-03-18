"""Shared console with logger adapter for dopemux.

This module provides a single, centralized Rich Console instance with a logger
adapter that all dopemux modules should use. This ensures consistent formatting
and prevents AttributeError when accessing console.logger.

Usage:
    from dopemux.console import console

    console.print("Hello!")
    console.logger.info("Info message")
    console.logger.error("Error message")
    console.logger.warning("Warning message")
"""

from rich.console import Console

from dopemux.ui.theme import create_console


class _ConsoleAdapter:
    """Adapter that provides .logger interface for Rich Console."""

    def __init__(self, console_instance: Console) -> None:
        self._console = console_instance

    def info(self, *args, **kwargs) -> None:
        """Log info message to console."""
        self._console.print(*args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        """Log error message to console with error styling."""
        self._console.print(*args, style="error", **kwargs)

    def warning(self, *args, **kwargs) -> None:
        """Log warning message to console with warning styling."""
        self._console.print(*args, style="warning", **kwargs)


# Single console instance with logger adapter - use this everywhere
console = create_console()
console.logger = _ConsoleAdapter(console)
