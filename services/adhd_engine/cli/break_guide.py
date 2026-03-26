"""
Interactive Break Guide
"""

import time
import sys
import threading
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.align import Align
from rich.text import Text

from services.shared.brand_voice import StatusChip, aftercare_text, brand_text, brand_title

console = Console()

def run_breathing_guide(duration_sec: int = 120):
    """Run a visual breathing guide."""
    cycles = duration_sec // 16  # 4+4+4+4 = 16s box breathing
    
    console.clear()
    console.print(Panel(brand_text("Micro-reset: box breathing. Follow the guide.", chip=StatusChip.AFTERCARE)))
    time.sleep(1)
    
    try:
        for i in range(cycles):
            # Inhale (4s)
            with Live(refresh_per_second=10) as live:
                for step in range(40):
                    width = 10 + int(step * 1.5)
                    live.update(Align.center(Panel(f"[bold green]Inhale...[/bold green]\n{'█' * width}", width=60)))
                    time.sleep(0.1)
            
            # Hold (4s)
            with Live(refresh_per_second=10) as live:
                for step in range(40):
                    live.update(Align.center(Panel(f"[bold yellow]Hold...[/bold yellow]\n{'█' * 70}", width=60)))
                    time.sleep(0.1)
            
            # Exhale (4s)
            with Live(refresh_per_second=10) as live:
                for step in range(40):
                    width = 70 - int(step * 1.5)
                    live.update(Align.center(Panel(f"[bold blue]Exhale...[/bold blue]\n{'█' * width}", width=60)))
                    time.sleep(0.1)
            
            # Hold (4s)
            with Live(refresh_per_second=10) as live:
                for step in range(40):
                    live.update(Align.center(Panel(f"[bold yellow]Hold...[/bold yellow]\n{'█' * 10}", width=60)))
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        pass
        
    console.print(f"\n{aftercare_text('Reset complete. Welcome back.')}\n")

def interactive_break_menu():
    """Show interactive break menu."""
    console.clear()
    console.print(Panel(brand_title("Break menu", chip=StatusChip.AFTERCARE)))
    
    console.print("1. [bold cyan]🧘 Micro-Reset[/bold cyan] (2m)  [Brain fog / Anxiety]")
    console.print("2. [bold blue]💧 Hydration[/bold blue]   (5m)  [Thirsty / Stiff]")
    console.print("3. [bold green]🚶 Movement[/bold green]    (15m) [Restless / Energy dip]")
    console.print("4. [bold yellow]🛌 Deep Rest[/bold yellow]   (20m) [Exhausted / Overwhelmed]")
    console.print("q. Cancel")
    
    choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "q"], default="1")
    
    if choice == "q":
        return
    
    if choice == "1":
        run_breathing_guide(120)
    elif choice == "2":
        console.print(f"\n{brand_text('Hydration break. Go get a glass of water and stretch.', chip=StatusChip.AFTERCARE)}")
        _timer(300, "Hydration Break")
    elif choice == "3":
        console.print(f"\n{brand_text('Movement break. Walk around, do pushups, or dance.', chip=StatusChip.AFTERCARE)}")
        _timer(900, "Movement Break")
    elif choice == "4":
        console.print(f"\n{brand_text('Deep rest. Close your eyes and do nothing for a minute.', chip=StatusChip.AFTERCARE)}")
        _timer(1200, "Deep Rest")

def _notify(title, message):
    """Send system notification via osascript."""
    import subprocess
    try:
        script = f'display notification "{message}" with title "{title}" sound name "Glass"'
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception:
        pass

def _timer(seconds, title="Break"):
    """Simple countdown timer with notification."""
    import time
    from rich.live import Live
    from rich.align import Align
    from rich.panel import Panel
    
    total = seconds
    try:
        with Live(refresh_per_second=1) as live:
            while seconds > 0:
                mins, secs = divmod(seconds, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                percent = 1 - (seconds / total)
                
                # Color changes as time runs out
                color = "green"
                if percent > 0.5: color = "yellow"
                if percent > 0.8: color = "red"
                
                live.update(Align.center(
                    Panel(
                        f"[bold {color}]{time_str}[/bold {color}]\n" + 
                        f"[{color}]{'█' * int(percent * 40)}{'░' * (40 - int(percent * 40))}[/{color}]",
                        title=f"[bold]{title}[/bold]",
                        width=50
                    )
                ))
                time.sleep(1)
                seconds -= 1
        
        console.print(aftercare_text(f"{title} complete. Welcome back."))
        _notify(
            brand_title("Dopemux break", chip=StatusChip.AFTERCARE),
            brand_text(f"{title} complete. Time to refocus.", chip=StatusChip.AFTERCARE),
        )
        
        # Play sound on mac
        import subprocess
        subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], check=False)
        
    except KeyboardInterrupt:
        console.print(f"\n{brand_text(f'{title} ended early.', chip=StatusChip.EDGE)}")
