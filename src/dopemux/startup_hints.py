"""
Startup hints and feature tips for Dopemux.

Shows rotating feature hints on every startup with rich colors and animations.
"""
import random
from typing import List, Dict
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# Comprehensive feature database
DOPEMUX_FEATURES = [
    {
        "emoji": "🔥",
        "title": "DOPE Layout",
        "description": "Full monitoring experience with orchestrator + dual agents",
        "usage": "dopemux dope --theme muted",
        "category": "Quick Start",
        "color": "red"
    },
    {
        "emoji": "⚡",
        "title": "Quick Launch",
        "description": "Fastest way to start - simple layout, instant coding",
        "usage": "dopemux quick",
        "category": "Quick Start",
        "color": "yellow"
    },
    {
        "emoji": "🌳",
        "title": "Git Worktrees",
        "description": "Parallel development without branch switching chaos",
        "usage": "dopemux worktrees create feature/new",
        "category": "Workflow",
        "color": "green"
    },
    {
        "emoji": "🧠",
        "title": "ADHD Engine",
        "description": "Real-time energy/attention tracking with break suggestions",
        "usage": "Automatic - monitors cognitive load & suggests breaks",
        "category": "ADHD Features",
        "color": "magenta"
    },
    {
        "emoji": "📊",
        "title": "ADHD Dashboard",
        "description": "Visualize your energy patterns and session analytics",
        "usage": "http://localhost:8097/api/metrics",
        "category": "ADHD Features",
        "color": "cyan"
    },
    {
        "emoji": "💾",
        "title": "Context Preservation",
        "description": "Never lose your train of thought - save/restore context",
        "usage": "dopemux save (auto-saves with context manager)",
        "category": "Productivity",
        "color": "blue"
    },
    {
        "emoji": "🔍",
        "title": "Semantic Code Search",
        "description": "AI-powered search across code + docs with complexity scoring",
        "usage": "Uses dope-context MCP server automatically",
        "category": "Search",
        "color": "green"
    },
    {
        "emoji": "📝",
        "title": "Decision Tracking",
        "description": "Log architectural decisions with rationale to ConPort",
        "usage": "dopemux decisions list --workspace .",
        "category": "Knowledge Graph",
        "color": "blue"
    },
    {
        "emoji": "🏥",
        "title": "Health Checks",
        "description": "Comprehensive system diagnostics for all services",
        "usage": "dopemux health",
        "category": "Maintenance",
        "color": "green"
    },
    {
        "emoji": "🎯",
        "title": "Multi-Instance",
        "description": "Run multiple isolated Claude sessions simultaneously",
        "usage": "dopemux instances create (manages worktree instances)",
        "category": "Advanced",
        "color": "cyan"
    },
    {
        "emoji": "🤖",
        "title": "MCP Servers",
        "description": "9 MCP servers: ConPort, Serena, PAL, Zen, and more",
        "usage": "dopemux mcp status (manage all MCP servers)",
        "category": "MCP",
        "color": "yellow"
    },
    {
        "emoji": "🧪",
        "title": "PAL API Lookup",
        "description": "Latest API/SDK docs with OS/framework version detection",
        "usage": "Ask Claude: 'What's the latest SwiftUI API?'",
        "category": "MCP",
        "color": "magenta"
    },
    {
        "emoji": "⏱️",
        "title": "Statusline HUD",
        "description": "Live development metrics in your tmux status bar",
        "usage": "Shows energy ⚡, attention 👁️, breaks ☕, tokens",
        "category": "UI",
        "color": "cyan"
    },
    {
        "emoji": "🎨",
        "title": "Visual Themes",
        "description": "Multiple color schemes: muted, neon, house, gruvbox",
        "usage": "dopemux dope --theme neon",
        "category": "UI",
        "color": "magenta"
    },
    {
        "emoji": "☕",
        "title": "Break Reminders",
        "description": "Proactive break suggestions after 25-min focus sessions",
        "usage": "Automatic - prevents ADHD burnout",
        "category": "ADHD Features",
        "color": "yellow"
    },
    {
        "emoji": "🔄",
        "title": "Restore Context",
        "description": "Resume your last session with all context preserved",
        "usage": "dopemux restore",
        "category": "Productivity",
        "color": "blue"
    },
    {
        "emoji": "📐",
        "title": "Tmux Layouts",
        "description": "Pre-built layouts with examples and documentation",
        "usage": "dopemux layouts (shows: low, medium, dope, full)",
        "category": "UI",
        "color": "green"
    },
    {
        "emoji": "🎭",
        "title": "Role Personas",
        "description": "Specialized AI personas: developer, architect, researcher",
        "usage": "dopemux start --role developer",
        "category": "AI",
        "color": "magenta"
    },
    {
        "emoji": "📦",
        "title": "Docker Backups",
        "description": "One-command backup of all volumes and state",
        "usage": "dopemux backup",
        "category": "Maintenance",
        "color": "blue"
    },
    {
        "emoji": "🛡️",
        "title": "Main Branch Protection",
        "description": "Prevents accidental work on main - suggests worktrees",
        "usage": "Automatic - prompts when uncommitted on main",
        "category": "Safety",
        "color": "red"
    },
    {
        "emoji": "🔌",
        "title": "LiteLLM Routing",
        "description": "Route to 13+ models: GPT-5, Grok, Claude, DeepSeek",
        "usage": "export ANTHROPIC_BASE_URL=http://localhost:4000",
        "category": "AI",
        "color": "yellow"
    },
    {
        "emoji": "🧭",
        "title": "Workspace Isolation",
        "description": "Separate cognitive state per project workspace",
        "usage": "dopemux start --workspace ~/code/project",
        "category": "Workflow",
        "color": "green"
    },
    {
        "emoji": "📱",
        "title": "Mobile Notifications",
        "description": "Test/build completion alerts to your phone via Happy",
        "usage": "dopemux run-tests (sends results to mobile)",
        "category": "Integrations",
        "color": "cyan"
    },
    {
        "emoji": "🎬",
        "title": "Session Recording",
        "description": "Automatic session recording to ConPort knowledge graph",
        "usage": "dopemux decisions list (query recorded sessions)",
        "category": "Knowledge Graph",
        "color": "blue"
    },
    {
        "emoji": "🏥",
        "title": "System Diagnostics",
        "description": "Dr. Dopemux runs comprehensive health checks",
        "usage": "dopemux doctor (diagnoses all services)",
        "category": "Maintenance",
        "color": "green"
    },
    {
        "emoji": "🔬",
        "title": "Code Analysis",
        "description": "Multi-angle document processing with ADHD patterns",
        "usage": "dopemux analyze (deep codebase analysis)",
        "category": "Search",
        "color": "cyan"
    },
    {
        "emoji": "🧩",
        "title": "Profile Manager",
        "description": "Multi-project configuration profiles",
        "usage": "dopemux profile list (manage profiles)",
        "category": "Advanced",
        "color": "magenta"
    },
    {
        "emoji": "🪝",
        "title": "Hook System",
        "description": "Customize Claude Code integration with hooks",
        "usage": "dopemux hooks list (manage hooks)",
        "category": "Advanced",
        "color": "yellow"
    },
    {
        "emoji": "🛡️",
        "title": "Safe Mode",
        "description": "Safety hooks prevent dangerous operations",
        "usage": "dopemux safe status (check safety hooks)",
        "category": "Safety",
        "color": "red"
    },
    {
        "emoji": "🤖",
        "title": "Autoresponder",
        "description": "Claude auto-responds to continue conversations",
        "usage": "dopemux autoresponder status",
        "category": "AI",
        "color": "cyan"
    },
    {
        "emoji": "📱",
        "title": "Happy Mobile Client",
        "description": "Smartphone companion for dev notifications",
        "usage": "dopemux mobile setup (iOS/Android)",
        "category": "Integrations",
        "color": "magenta"
    },
    {
        "emoji": "🏗️",
        "title": "Build Notifications",
        "description": "Get notified when builds complete",
        "usage": "dopemux run-build 'npm run build'",
        "category": "Integrations",
        "color": "yellow"
    },
    {
        "emoji": "📄",
        "title": "Document Extraction",
        "description": "Extract structured data from chatlogs with ADHD patterns",
        "usage": "dopemux extract (ADHD-optimized parsing)",
        "category": "Productivity",
        "color": "blue"
    },
    {
        "emoji": "🔧",
        "title": "Dev Mode",
        "description": "Development tooling for Dopemux contributors",
        "usage": "dopemux dev (contributor commands)",
        "category": "Advanced",
        "color": "dim"
    },
]


def get_random_hint() -> Dict[str, str]:
    """Get a random feature hint."""
    return random.choice(DOPEMUX_FEATURES)


def get_hint_by_category(category: str) -> List[Dict[str, str]]:
    """Get all hints from a specific category."""
    return [f for f in DOPEMUX_FEATURES if f["category"] == category]


def create_hint_banner(hint: Dict[str, str] = None, width: int = 80) -> Panel:
    """
    Create a beautiful animated hint banner.
    
    Args:
        hint: Feature hint dict (random if None)
        width: Banner width
        
    Returns:
        Rich Panel with animated hint
    """
    if hint is None:
        hint = get_random_hint()
    
    # Create gradient title
    title = Text()
    title.append("💡 ", style="bold yellow")
    title.append("Dopemux Tip", style="bold cyan")
    title.append(" • ", style="dim")
    title.append(hint["category"], style=f"bold {hint['color']}")
    
    # Create content grid
    content = Table.grid(padding=(0, 1))
    content.add_column(style="bold", justify="left", width=4)
    content.add_column(style="", justify="left")
    
    # Feature name with emoji
    feature_line = Text()
    feature_line.append(hint["emoji"] + " ", style="bold")
    feature_line.append(hint["title"], style=f"bold {hint['color']}")
    
    content.add_row("", feature_line)
    content.add_row("", "")
    
    # Description
    desc_text = Text(hint["description"], style="dim white")
    content.add_row("📖", desc_text)
    content.add_row("", "")
    
    # Usage with command styling
    usage_line = Text()
    usage_line.append("▸ ", style=f"bold {hint['color']}")
    usage_line.append(hint["usage"], style=f"{hint['color']}")
    content.add_row("⚡", usage_line)
    
    # Create panel with gradient border
    panel = Panel(
        content,
        title=title,
        border_style=hint["color"],
        padding=(0, 2),
        expand=False
    )
    
    return panel


def create_feature_list_banner() -> Panel:
    """Create a banner showing all feature categories."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold cyan", justify="left")
    content.add_column(style="dim", justify="right")
    
    # Count features by category
    categories = {}
    for feature in DOPEMUX_FEATURES:
        cat = feature["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    content.add_row("[bold yellow]💡 Dopemux Features[/bold yellow]", "")
    content.add_row("", "")
    
    category_emojis = {
        "Quick Start": "🚀",
        "Workflow": "🔄",
        "ADHD Features": "🧠",
        "Productivity": "⚡",
        "Search": "🔍",
        "Knowledge Graph": "📊",
        "Maintenance": "🏥",
        "Advanced": "🎯",
        "MCP": "🤖",
        "UI": "🎨",
        "AI": "🎭",
        "Safety": "🛡️",
        "Integrations": "🔌",
    }
    
    for cat, count in sorted(categories.items()):
        emoji = category_emojis.get(cat, "📁")
        content.add_row(
            f"{emoji} {cat}",
            f"[dim]{count} features[/dim]"
        )
    
    return Panel(
        content,
        title="[bold cyan]Feature Categories[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )


if __name__ == "__main__":
    # Test the banner
    from rich.console import Console
    
    console = Console()
    console.print()
    console.print(create_hint_banner())
    console.print()
    console.print(create_feature_list_banner())
    console.print()
