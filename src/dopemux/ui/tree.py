"""Beautiful Tree Rendering for Dopemux CLI.

Provides high-contrast, themed tree visualizations for complex repository
hierarchies and execution traces.
"""

from rich.tree import Tree
from rich.console import RenderableType
from .theme import Glyphs, RITUAL_CYAN, SERUM_MINT, GREMLIN_PINK

def create_truth_tree(title: str = "Repo Truth Trace") -> Tree:
    """Create a pre-styled tree for truth pack visualization."""
    return Tree(
        f"[mint]{Glyphs.BRAND_MARK} {title}[/]",
        guide_style=f"bold {RITUAL_CYAN}",
        highlight=True,
    )

def add_phase_node(tree: Tree, phase_id: str, label: str, status: str = "pending") -> Tree:
    """Add a themed phase node to the tree."""
    glyph = Glyphs.PENDING
    style = "text.dim"
    
    if status == "success":
        glyph = Glyphs.SUCCESS
        style = "success"
    elif status == "running":
        glyph = Glyphs.RUNNING
        style = "mint.bright"
    elif status == "error":
        glyph = Glyphs.ERROR
        style = "error"
        
    node_label = f"[{style}]Phase {phase_id}: {label} {glyph}[/]"
    return tree.add(node_label)

def add_file_node(parent: Tree, filename: str, is_trace: bool = False) -> None:
    """Add a file leaf to a tree node."""
    glyph = Glyphs.CODE
    style = "text"
    
    if is_trace:
        glyph = Glyphs.WRENCH
        style = "violet"
        
    parent.add(f"[{style}]{glyph} {filename}[/]")
