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
        if not args:
            return
            
        first = args[0]
        # Only prefix if it's a string and doesn't already have a ritual prefix
        if isinstance(first, str):
            if not any(first.startswith(p) for p in ["[mint]", "[text.dim]", "[info]", "[success]", "[warning]", "[error]", "[bold", "[blue", "[green", "[red", "[yellow", "━━━"]):
                args = (f"[mint][TELEMETRY][/mint] {first}",) + args[1:]
        
        self._console.print(*args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        """Log error message to console with error styling."""
        if not args:
            return
            
        first = args[0]
        if isinstance(first, str):
            if not any(first.startswith(p) for p in ["[error]", "[BLOCKER]", "❌", "[red", "[bold red"]):
                args = (f"[gremlin.pink][BLOCKER][/gremlin.pink] {first}",) + args[1:]
        
        self._console.print(*args, style="error", **kwargs)

    def warning(self, *args, **kwargs) -> None:
        """Log warning message to console with warning styling."""
        if not args:
            return
            
        first = args[0]
        if isinstance(first, str):
            if not any(first.startswith(p) for p in ["[warning]", "[HAZARD]", "⚠️", "⚠", "[yellow", "[bold yellow"]):
                args = (f"[gilt.edge][HAZARD][/gilt.edge] {first}",) + args[1:]
        
        self._console.print(*args, style="warning", **kwargs)

    def debug(self, *args, **kwargs) -> None:
        """Log debug message to console."""
        if not args:
            return
            
        first = args[0]
        if isinstance(first, str):
            if not any(first.startswith(p) for p in ["[debug]", "[SIGNAL]"]):
                args = (f"[text.dim][SIGNAL][/text.dim] {first}",) + args[1:]
        
        self._console.print(*args, style="text.dim", **kwargs)


# Single console instance with logger adapter - use this everywhere
console = create_console()
console.logger = _ConsoleAdapter(console)
