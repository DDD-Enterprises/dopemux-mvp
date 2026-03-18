"""
AI Personas CLI Commands.

Management and discovery of specialized AI behavioral guidelines (personas).
"""

import click
from pathlib import Path
from ..console import console
from ..claude.instruction_manager import InstructionManager

@click.group("personas")
def personas():
    """AI Persona management and guidance libraries."""
    pass

@personas.command("list")
def personas_list():
    """List all available AI personas in the project."""
    manager = InstructionManager(Path.cwd())
    names = manager.list_personas()
    if not names:
        console.print("[info]No specialized personas found in .claude/personas/[/info]")
        return
        
    from rich.table import Table
    table = Table(title="Available AI Personas", border_style="mint")
    table.add_column("Persona Name", style="mint")
    table.add_column("Type", style="text.dim")
    
    for name in sorted(names):
        table.add_row(name, "Guideline (.agent.md)")
        
    console.print(table)

@personas.command("show")
@click.argument("name")
def personas_show(name: str):
    """Display the guidelines for a specific persona."""
    manager = InstructionManager(Path.cwd())
    content = manager.get_persona_content(name)
    if not content:
        console.print(f"[error]Persona '{name}' not found[/error]")
        return
        
    from rich.panel import Panel
    from rich.markdown import Markdown
    console.print(Panel(Markdown(content), title=f"Persona: {name}", border_style="mint"))
