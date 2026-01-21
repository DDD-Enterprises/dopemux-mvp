#!/usr/bin/env python3
"""
ADHD-Friendly Error Messages

Clear, actionable error messages with progressive disclosure and visual clarity.

Design Principles:
- Lead with the problem (what went wrong)
- Explain why it matters (impact)
- Provide step-by-step fix (actionable)
- Use visual hierarchy (emojis, colors, formatting)
- Avoid technical jargon where possible

Target: < 3 seconds to understand the issue and know what to do
"""

from typing import Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


class ADHDErrorMessage:
    """
    ADHD-optimized error message builder.

    **Structure**:
    1. 🚨 Problem (clear, concise)
    2. ❓ Why it matters (impact)
    3. ✅ How to fix (step-by-step)
    4. 💡 Optional: Additional context
    """

    def __init__(
        self,
        problem: str,
        why: str,
        fix: List[str],
        context: Optional[str] = None
    ):
        """
        Create ADHD-friendly error message.

        Args:
            problem: What went wrong (concise)
            why: Why it matters (impact)
            fix: Step-by-step fix instructions
            context: Optional additional context
        """
        self.problem = problem
        self.why = why
        self.fix = fix
        self.context = context

    def show(self):
        """Display error message with ADHD-friendly formatting."""
        # Build message
        text = Text()

        # Problem (red, bold)
        text.append("🚨 PROBLEM\n", style="bold red")
        text.append(f"{self.problem}\n\n", style="red")

        # Why it matters (yellow)
        text.append("❓ WHY IT MATTERS\n", style="bold yellow")
        text.append(f"{self.why}\n\n", style="yellow")

        # How to fix (green)
        text.append("✅ HOW TO FIX\n", style="bold green")
        for i, step in enumerate(self.fix, 1):
            text.append(f"{i}. {step}\n", style="green")

        # Optional context (dim)
        if self.context:
            text.append("\n💡 ADDITIONAL INFO\n", style="bold dim")
            text.append(f"{self.context}", style="dim")

        # Display in panel
        panel = Panel(
            text,
            title="[bold red]Error[/bold red]",
            border_style="red",
            padding=(1, 2)
        )

        console.logger.info(panel)


# Common Error Messages Library
# =============================================================================

WORKTREE_ERRORS: Dict[str, ADHDErrorMessage] = {
    "workspace_not_found": ADHDErrorMessage(
        problem="Can't find workspace root directory",
        why="Dopemux needs to know where your project is to configure MCP servers correctly",
        fix=[
            "Make sure you're inside a git repository: run 'git status'",
            "If not in a git repo, navigate to your project directory",
            "If you ARE in a git repo, this might be a bug - run 'dopemux doctor --worktree -v'"
        ],
        context="Workspace detection tries (in order): env var → git command → project markers → current directory"
    ),

    "mcp_config_missing": ADHDErrorMessage(
        problem="~/.claude.json configuration file not found",
        why="Claude Code needs this file to know which MCP servers to use",
        fix=[
            "Create .claude.json by running 'dopemux start' once",
            "Or manually create it following Claude Code documentation",
            "Check that you have write permissions to your home directory"
        ],
        context=".claude.json stores your Claude Code settings including MCP server configurations"
    ),

    "worktree_not_git": ADHDErrorMessage(
        problem="Current directory is not a git worktree",
        why="Worktree features only work in git repositories with worktrees enabled",
        fix=[
            "Check if you're in a git repo: run 'git status'",
            "To create a worktree: run 'git worktree add /path branch-name'",
            "Or use dopemux: run 'dopemux start' and follow the multi-instance prompts"
        ],
        context="Git worktrees let you work on multiple branches simultaneously without switching"
    ),

    "shell_integration_missing": ADHDErrorMessage(
        problem="Shell integration not installed",
        why="Without shell integration, 'dwt' command won't work for worktree switching",
        fix=[
            "Install for bash: run 'dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc'",
            "Install for zsh: run 'dopemux shell-setup zsh >> ~/.zshrc && source ~/.zshrc'",
            "Then test with: dwt <branch-name>"
        ],
        context="Shell integration adds the 'dwt', 'dwtls', and 'dwtcur' commands to your shell"
    ),

    "auto_config_failed": ADHDErrorMessage(
        problem="Automatic MCP configuration failed",
        why="Your MCP servers won't be properly isolated for this worktree",
        fix=[
            "Run 'dopemux doctor --worktree -v' to see what went wrong",
            "Check that .claude.json has a section for your workspace",
            "Try manual configuration as fallback: check docs/WORKTREE_MCP_SETUP.md"
        ],
        context="Auto-configuration updates ConPort and Dope-Context settings for workspace isolation"
    ),

    "template_copy_failed": ADHDErrorMessage(
        problem="Failed to copy template files to worktree",
        why="Your worktree might be missing important project configuration",
        fix=[
            "Check file permissions in the worktree directory",
            "Verify main repository path is accessible",
            "Manually copy needed files from main repo if necessary"
        ],
        context="Templates include .dopemux/, linting configs, and editor settings (not personal data)"
    ),

    "legacy_mode_active": ADHDErrorMessage(
        problem="Legacy detection mode is enabled",
        why="You're not getting the benefits of the improved worktree system",
        fix=[
            "Disable legacy mode: unset DOPEMUX_LEGACY_DETECTION environment variable",
            "Or set it to 0: export DOPEMUX_LEGACY_DETECTION=0",
            "Remove from .bashrc/.zshrc if set there permanently"
        ],
        context="Legacy mode disables auto-configuration and uses old workspace detection"
    ),

    "docker_not_available": ADHDErrorMessage(
        problem="Docker is not running or not available",
        why="MCP servers (ConPort, Serena, Zen, etc.) run in Docker containers",
        fix=[
            "Start Docker Desktop application",
            "Wait 10-15 seconds for Docker to fully start",
            "Verify with: docker ps",
            "If still broken, try: docker restart $(docker ps -q)"
        ],
        context="Dopemux uses Docker for consistent MCP server environments across worktrees"
    ),

    "api_key_missing": ADHDErrorMessage(
        problem="Required API key not set",
        why="Some MCP servers need API keys to function (Context7, Voyage, etc.)",
        fix=[
            "Add to .env file: echo 'YOUR_API_KEY=xxx' >> .env",
            "Or export in shell: export YOUR_API_KEY=xxx",
            "Then restart dopemux: dopemux start"
        ],
        context="API keys are never committed to git - they're personal and project-specific"
    ),
}


def show_error(error_key: str, **kwargs):
    """
    Show a predefined ADHD-friendly error message.

    Args:
        error_key: Error identifier from WORKTREE_ERRORS
        **kwargs: Additional context to interpolate into message
    """
    if error_key not in WORKTREE_ERRORS:
        console.logger.error(f"[red]Unknown error: {error_key}[/red]")
        return

    error = WORKTREE_ERRORS[error_key]
    error.show()


def show_custom_error(problem: str, why: str, fix: List[str], context: Optional[str] = None):
    """
    Show a custom ADHD-friendly error message.

    Args:
        problem: What went wrong
        why: Why it matters
        fix: Step-by-step fix instructions
        context: Optional additional context
    """
    error = ADHDErrorMessage(problem, why, fix, context)
    error.show()
