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

@contextmanager
def branded_progress(
    *columns: Any,
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

    # If columns are provided, use them. Otherwise use defaults.
    if not columns:
        columns = (
            SpinnerColumn(spinner_name="dots", style="mint"),
            TextColumn("[mint]{task.description}[/mint]"),
            BarColumn(complete_style="mint", finished_style="mint.soft"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        )

    progress = Progress(
        *columns,
        console=console,
        transient=transient,
        **kwargs
    )
    
    try:
        progress.start()
        yield progress
    finally:
        progress.stop()
