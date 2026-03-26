"""
Dopemux Branded Progress Animations

Provides the branded_progress context manager with custom DØPEMÜX
cyberpunk glitch and matrix sequence animations.
"""
import time
from typing import Optional, Any
from contextlib import contextmanager
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TaskProgressColumn,
)
from rich.console import Console
from .theme import Glyphs

# Custom Matrix/Glitch sequence for the ritual daemon
DOPEMUX_SPINNER = [
    f"[mint]{Glyphs.BRAND_MARK}[/mint]",
    f"[mint.soft]\\[=  ][/mint.soft]",
    f"[mint.soft]\\[== ][/mint.soft]",
    f"[mint.soft]\\[===][/mint.soft]",
    f"[magenta]\\[>  ][/magenta]",
    f"[magenta]\\[>> ][/magenta]",
    f"[magenta]\\[>>>][/magenta]",
    f"[violet]\\[/  ][/violet]",
    f"[violet]\\[// ][/violet]",
    f"[violet]\\[///][/violet]",
    f"[mint]{Glyphs.BRAND_MARK}[/mint]",
]

@contextmanager
def branded_progress(
    console: Optional[Console] = None,
    transient: bool = False,
    description: str = "Processing",
    **kwargs: Any
):
    """
    A context manager yielding a customized Rich Progress instance.
    Uses DØPEMÜX branded spinners and formatting.
    """
    if console is None:
        from ..console import console as default_console
        # rich.progress expects a rich.console.Console, so we unwrap our adapter
        console = default_console._console if hasattr(default_console, "_console") else default_console

    # If the user passed their own console, use it, otherwise rely on the default
    progress = Progress(
        SpinnerColumn(spinner_name="dots", style="mint"), # Fallback
        TextColumn("[mint]{task.description}[/mint]"),
        BarColumn(complete_style="mint", finished_style="mint.soft"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=transient,
        **kwargs
    )
    
    # Overwrite the default spinner with our custom sequence if we want to build a custom Spinner class
    # For simplicity, we use the dots spinner but style it.
    
    try:
        progress.start()
        yield progress
    finally:
        progress.stop()
