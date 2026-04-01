import time
from rich.live import Live
from rich.text import Text
from .theme import Glyphs

def boot_sequence():
    """Display a cyber-themed boot sequence."""
    messages = [
        ("INITIALIZING CORE SENSORS", "READY", "mint"),
        ("SYNCHRONIZING ATTENTION MAP", "ALIGNED", "info"),
        ("LOADING WORKTREE ISOLATION", "ENGAGED", "warning"),
        ("PRIMING RITUAL CHAMBER", "STABLE", "violet"),
    ]
    
    current_text = Text()
    current_text.append(f"\n{Glyphs.INFO} [bold]DØPEMÜX CORE SYSTEM IGNITION[/bold]\n", style="heading")
    
    with Live(current_text, refresh_per_second=10, transient=True) as live:
        live.update(current_text)
        time.sleep(0.4)
        
        for msg, status, color in messages:
            current_text.append("\n")
            current_text.append(f"{Glyphs.SUCCESS} {msg} ", style="text.dim")
            live.update(current_text)
            time.sleep(0.3)
            current_text.append(f"[{status}]", style=f"bold {color}")
            live.update(current_text)
            time.sleep(0.2)
            
        current_text.append("\n\n" + "="*40 + "\n", style="text.dim")
        current_text.append(f"{Glyphs.RUNNING} [bold]SYSTEM LIVE - RITUAL COMMENCING[/bold]\n", style="mint")
        live.update(current_text)
        time.sleep(0.8)
