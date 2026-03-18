import sys
from enum import Enum, auto
from typing import List, Dict, Any, Optional


class RenderMode(Enum):
    RICH = auto()
    FULL = auto()
    COMPACT = auto()
    PLAIN = auto()


def detect_render_mode() -> RenderMode:
    """Heuristically determine the best render mode for the current terminal."""
    if not sys.stdout.isatty():
        return RenderMode.PLAIN
    
    # Try to get terminal size
    try:
        import shutil
        columns, _ = shutil.get_terminal_size()
        if columns < 80:
            return RenderMode.COMPACT
    except:
        pass
        
    return RenderMode.RICH


class RichTerminalRenderer:
    """Provides spaceage terminal rendering with color and structural elements."""

    def __init__(self, mode: Optional[RenderMode] = None, use_color: bool = True):
        self.mode = mode or RenderMode.FULL
        self.use_color = use_color
        self.colors = {
            "CRITICAL": "\033[1;31m",
            "HIGH": "\033[31m",
            "MEDIUM": "\033[33m",
            "LOW": "\033[36m",
            "INFO": "\033[32m",
            "RESET": "\033[0m"
        }

    def badge(self, status: str, severity: str = "INFO") -> str:
        """Render a status chip/badge."""
        color = self.colors.get(severity, self.colors["INFO"]) if self.use_color else ""
        reset = self.colors["RESET"] if self.use_color else ""
        return f"{color}[ {status:^8} ]{reset}"

    def table(self, title: str, headers: List[str], rows: List[List[Any]]):
        """Render a clean monospace table."""
        print(f"\n══ {title} ══")
        
        # Calculate widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))
        
        # Header
        header_line = " | ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers))
        print(header_line)
        print("-" * (sum(widths) + (len(headers) - 1) * 3))
        
        # Rows
        for row in rows:
            print(" | ".join(f"{str(val):<{widths[i]}}" for i, val in enumerate(row)))

    def timeline(self, stages: List[str], active_index: int):
        """Render a step-based progress timeline."""
        output = "\n"
        for i, stage in enumerate(stages):
            if i == active_index:
                color = self.colors["MEDIUM"] if self.use_color else ""
                output += f" {color}[{stage}]{self.colors['RESET'] if self.use_color else ''}"
            else:
                output += f"  {stage}  "
            
            if i < len(stages) - 1:
                output += " ➔ "
        print(output + "\n")

    def card(self, title: str, content: Dict[str, Any]):
        """Render a grouped summary card."""
        print(f"\n┌── {title} ──────────────────────────────────────")
        for key, value in content.items():
            print(f"│ {key:<15}: {value}")
        print("└──────────────────────────────────────────────")

    def mission_header_card(self, pr_id: str, repo: str, state: str, posture: str, risk: str, confidence: str, mission_line: str, return_obj: bool = False) -> Any:
        """Render the primary mission intelligence header."""
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column()
        
        table.add_row("PR ID", f"#{pr_id}")
        table.add_row("REPO", repo)
        table.add_row("STATUS", Text(state, style="bold green" if state == "READY" else "bold red"))
        table.add_row("POSTURE", Text(posture, style="bold magenta"))
        table.add_row("RISK", Text(risk, style="bold yellow" if risk != "LOW" else "green"))
        table.add_row("CONF", Text(confidence, style="bold cyan"))
        
        panel = Panel(table, title=f"MISSION INTEL: PR #{pr_id}", subtitle=mission_line, border_style="cyan")
        if return_obj: return panel
        print(panel)

    def strategy_comparison_table(self, strategy_library: Dict[str, Any], selected_id: str, return_obj: bool = False) -> Any:
        """Render a table comparing integration strategies."""
        from rich.table import Table
        from rich.panel import Panel
        
        table = Table(box=None, padding=(0, 1))
        table.add_column("Strategy", style="bold cyan")
        table.add_column("Risk", style="dim")
        table.add_column("Description")
        
        for sid, strat in strategy_library.items():
            style = "bold yellow" if sid == selected_id else "dim"
            table.add_row(
                strat.name if hasattr(strat, 'name') else sid,
                strat.risk_profile if hasattr(strat, 'risk_profile') else "N/A",
                strat.description if hasattr(strat, 'description') else "N/A",
                style=style
            )
            
        panel = Panel(table, title="STRATEGY ADJUDICATION", border_style="yellow")
        if return_obj: return panel
        print(panel)

    def blocker_table(self, blockers: List[Any], return_obj: bool = False) -> Any:
        """Render a list of active blockers."""
        from rich.table import Table
        from rich.panel import Panel
        
        table = Table(box=None)
        table.add_column("Type", style="bold red")
        table.add_column("Description")
        
        for b in blockers:
            b_type = b.type if hasattr(b, 'type') else b.get('type', 'UNKNOWN')
            b_desc = b.description if hasattr(b, 'description') else b.get('description', 'N/A')
            table.add_row(b_type, b_desc)
            
        panel = Panel(table, title="ACTIVE BLOCKERS", border_style="red")
        if return_obj: return panel
        print(panel)

    def stage_progress_rail(self, stages: List[Any]):
        """Render a detailed progress rail for stages."""
        from rich.console import Console
        from rich.text import Text
        
        output = Text()
        for i, stage in enumerate(stages):
            name = stage.name if hasattr(stage, 'name') else str(stage)
            status = stage.status if hasattr(stage, 'status') else "PENDING"
            
            color = "green" if status == "SUCCESS" else "yellow" if status == "IN_PROGRESS" else "red" if status == "FAILURE" else "dim"
            output.append(f" {name} ", style=color)
            if i < len(stages) - 1:
                output.append(" ➔ ", style="dim")
        
        print("\nREMEDIATION FLOW:")
        Console().print(output)

    def signoff_panel(self, action_class: str, required: bool, owner: str, state: str, last_timestamp: str):
        """Render a formal sign-off panel."""
        from rich.panel import Panel
        from rich.text import Text
        
        content = Text.assemble(
            ("ACTION   : ", "bold cyan"), f"{action_class}\n",
            ("REQUIRED : ", "bold cyan"), f"{'YES' if required else 'NO'}\n",
            ("OWNER    : ", "bold cyan"), f"{owner}\n",
            ("STATE    : ", "bold cyan"), (state, "bold green"), f"\n",
            ("STAMP    : ", "bold cyan"), last_timestamp
        )
        print(Panel(content, title="OPERATOR SIGNOFF", border_style="green"))

    def next_action_card(self, command: str, reason: str, severity: str):
        """Render the next recommended action."""
        from rich.panel import Panel
        from rich.text import Text
        
        color = "red" if severity == "HIGH" else "yellow" if severity == "MEDIUM" else "green"
        content = Text.assemble(
            ("COMMAND : ", "bold cyan"), f"{command}\n",
            ("REASON  : ", "bold cyan"), reason
        )
        print(Panel(content, title="NEXT ACTION", border_style=color))
