#!/usr/bin/env python3
"""
Project Initialization for Dopemux

Implements 'dopemux init' wizard that:
1. Auto-detects project type from markers
2. Suggests appropriate profile
3. Creates .dopemux/ directory structure
4. Sets active profile
5. Creates database directories
"""

from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from .profile_manager import ProfileManager

console = Console()


class ProjectInitializer:
    """Handles project initialization wizard."""

    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.dopemux_dir = self.workspace / ".dopemux"
        self.profile_manager = ProfileManager()

    def detect_project_type(self) -> Optional[str]:
        """
        Auto-detect project type from file markers.

        Returns:
            Suggested profile name or None
        """
        # Python ML/Data Science markers
        if any([
            (self.workspace / "requirements.txt").exists(),
            (self.workspace / "pyproject.toml").exists(),
            any(self.workspace.glob("*.ipynb")),
            (self.workspace / "notebooks").exists(),
        ]):
            # Check for ML/DS specific files
            if any([
                (self.workspace / "models").exists(),
                (self.workspace / "data").exists(),
                any(self.workspace.glob("**/train.py")),
            ]):
                return "python-ml"

        # Web development markers
        if any([
            (self.workspace / "package.json").exists(),
            (self.workspace / "tsconfig.json").exists(),
            (self.workspace / "next.config.js").exists(),
            (self.workspace / "vite.config.ts").exists(),
        ]):
            return "web-dev"

        # Rust
        if (self.workspace / "Cargo.toml").exists():
            return "adhd-default"  # No rust-specific profile yet

        # Go
        if (self.workspace / "go.mod").exists():
            return "adhd-default"

        # Generic Python
        if (self.workspace / "setup.py").exists() or (self.workspace / "pyproject.toml").exists():
            return "adhd-default"

        return None

    def initialize(self, profile_name: Optional[str] = None, force: bool = False) -> bool:
        """
        Run initialization wizard.

        Args:
            profile_name: Profile to use (prompts if None)
            force: Overwrite existing .dopemux/ directory

        Returns:
            True if successful
        """
        console.print(Panel.fit(
            "[bold cyan]🚀 Dopemux Project Initialization[/bold cyan]\n"
            f"Workspace: [dim]{self.workspace}[/dim]",
            border_style="cyan"
        ))

        # Check if already initialized
        if self.dopemux_dir.exists() and not force:
            console.print(f"\n[yellow]⚠️  Project already initialized (.dopemux/ exists)[/yellow]")

            if not Confirm.ask("Reinitialize?", default=False):
                console.print("[dim]Cancelled. Use --force to skip confirmation.[/dim]")
                return False

        # Step 1: Profile selection
        if not profile_name:
            detected = self.detect_project_type()

            if detected:
                console.print(f"\n🔍 [bold]Detected project type:[/bold] {detected}")

                if Confirm.ask(f"Use profile '{detected}'?", default=True):
                    profile_name = detected
                else:
                    profile_name = self._prompt_profile_selection()
            else:
                console.print("\n[dim]Could not auto-detect project type[/dim]")
                profile_name = self._prompt_profile_selection()

        # Verify profile exists
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            console.print(f"\n[red]❌ Profile not found: {profile_name}[/red]")
            console.print("[dim]Run: dopemux profile list[/dim]")
            return False

        # Step 2: Create .dopemux/ structure
        console.print(f"\n📁 Creating .dopemux/ directory...")
        self.dopemux_dir.mkdir(exist_ok=True)
        (self.dopemux_dir / "databases").mkdir(exist_ok=True)

        # Step 3: Set active profile
        self.profile_manager.set_active_profile(self.workspace, profile_name)
        console.print(f"   Active profile: {profile_name}")

        # Step 4: Create config.yaml (optional project overrides)
        config_file = self.dopemux_dir / "config.yaml"
        if not config_file.exists():
            config_file.write_text("# Project-specific configuration overrides\n# Merged with profile settings\n")
            console.print(f"   Created: .dopemux/config.yaml")

        # Step 5: Summary
        console.print(f"\n✅ [bold green]Initialization complete![/bold green]")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  1. Review profile: [cyan]dopemux profile show[/cyan]")
        console.print(f"  2. Start dopemux: [cyan]dopemux start[/cyan]")
        console.print(f"  3. (Optional) Edit: [dim].dopemux/config.yaml[/dim]")

        return True

    def _prompt_profile_selection(self) -> str:
        """Prompt user to select a profile."""
        profiles = self.profile_manager.list_profiles()

        if not profiles:
            console.print("[yellow]No profiles available. Using 'adhd-default'[/yellow]")
            return "adhd-default"

        console.print("\n[bold]Available profiles:[/bold]")
        for i, p in enumerate(profiles, 1):
            console.print(f"  {i}. [cyan]{p.name}[/cyan] - {p.description}")

        choice = Prompt.ask(
            "\nSelect profile",
            choices=[str(i) for i in range(1, len(profiles) + 1)],
            default="1"
        )

        return profiles[int(choice) - 1].name


def init_project(workspace: Path, profile: Optional[str], force: bool) -> bool:
    """Run project initialization (called from CLI)."""
    initializer = ProjectInitializer(workspace)
    return initializer.initialize(profile, force)
