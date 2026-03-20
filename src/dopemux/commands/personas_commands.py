"""
AI Personas CLI Commands.

Management and discovery of specialized AI behavioral guidelines (personas).
"""

import click
from pathlib import Path
from ..console import console
from ..claude.instruction_manager import InstructionManager
from ..ui.theme import styled_panel, styled_table, Glyphs, StatusChip

@click.group("personas")
def personas():
    """
    🎭 Cognitive Personas: Management and discovery of AI behavioral guidelines

    Orchestrates the selection and application of specialized AI personas. 
    These guidelines define the cognitive voice and technical constraints of 
    the active daemon, ensuring consistent behavioral patterns across 
    different ritual contexts.
    """
    pass

@personas.command("list")
def personas_list():
    """
    📋 Catalog Archetypes: List all available AI personas in the project

    Displays the full index of registered personas, providing a map of 
    available cognitive behavioral guidelines (.agent.md).
    """
    manager = InstructionManager(Path.cwd())
    names = manager.list_personas()
    if not names:
        console.print("[info]No specialized personas found in .claude/personas/[/info]")
        return
        
    table = styled_table(
        "Available AI Personas",
        ("Persona Name", {"style": "mint"}),
        ("Type", {"style": "text.dim"}),
    )
    
    for name in sorted(names):
        table.add_row(name, "Guideline (.agent.md)")
        
    console.print(table)

@personas.command("show")
@click.argument("name")
def personas_show(name: str):
    """
    📄 Inspect Guideline: Display the guidelines for a specific persona

    Renders the complete cognitive specification for a single persona 
    archetype, detailing its prescribed behavioral rituals.
    """
    manager = InstructionManager(Path.cwd())
    content = manager.get_persona_content(name)
    if not content:
        console.print(f"[error]Persona '{name}' not found[/error]")
        return
        
    from rich.markdown import Markdown
    console.print(styled_panel(Markdown(content), title=f"Persona: {name}", border_style="panel.border"))
