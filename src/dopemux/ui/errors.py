"""
Dopemux Clinical Forensics Exception Handler

Hooks into sys.excepthook and Click's exception handling to render
high-fidelity, branded error output (VoiceMode.CLINICAL_FORENSICS).
"""
import sys
import traceback
from typing import Type, Any
import click
from rich.traceback import Traceback
from .theme import styled_panel, Glyphs
from ..console import console

def custom_excepthook(exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
    """
    Global unhandled exception hook for DØPEMÜX.
    Renders tracebacks using the clinical forensics voice and gremlin.pink styling.
    """
    # Prevent infinite recursion if the rich console itself crashes
    try:
        tb = Traceback.from_exception(
            exc_type, exc_value, exc_traceback, 
            show_locals=True,
            word_wrap=True,
            theme="monokai"
        )
        
        panel = styled_panel(
            tb,
            title=f"{Glyphs.ERROR} [gremlin.pink bold]CRITICAL RITUAL FAILURE[/gremlin.pink bold]",
            border_style="error"
        )
        console.print("
")
        console.print(panel)
        console.print("
[text.dim][BLOCKER] Core dump initiated. The Daemon requires immediate intervention.[/text.dim]
")
    except Exception:
        # Fallback to standard error
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


def install_error_handlers() -> None:
    """
    Activates the DØPEMÜX exception interception layers.
    """
    # 1. Override global excepthook for unhandled python crashes
    sys.excepthook = custom_excepthook
    
    # 2. Optionally, monkey-patch click's show method to intercept ClickException
    original_show = click.ClickException.show

    def branded_show(self, file=None):
        if file is None:
            file = sys.stderr
        
        # Don't try to use Rich if we are completely broken, but we assume it's safe
        try:
            panel = styled_panel(
                f"[error]{self.format_message()}[/error]",
                title=f"{Glyphs.WARNING} [bold error]RITUAL ABORTED[/bold error]",
                border_style="error"
            )
            console.print(panel)
        except Exception:
            original_show(self, file)

    click.ClickException.show = branded_show
