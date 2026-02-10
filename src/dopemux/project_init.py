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

import os

import logging

logger = logging.getLogger(__name__)

import tempfile
from pathlib import Path
from typing import Optional, List
import click
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from .console import console
from .profile_manager import ProfileManager, DopemuxProfile


class ProjectInitializer:
    """Handles project initialization wizard."""

    def __init__(self, workspace: Path):
        self.workspace = Path(os.path.abspath(str(workspace)))
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
            (self.workspace / "requirements.txt").is_file(),
            (self.workspace / "pyproject.toml").is_file(),
            any(self.workspace.glob("*.ipynb")),
            (self.workspace / "notebooks").is_dir(),
        ]):
            # Check for ML/DS specific files
            if any([
                (self.workspace / "models").is_dir(),
                (self.workspace / "data").is_dir(),
                any(self.workspace.glob("**/train.py")),
            ]):
                return "python-ml"

        # Web development markers
        if any([
            (self.workspace / "package.json").is_file(),
            (self.workspace / "tsconfig.json").is_file(),
            (self.workspace / "next.config.js").is_file(),
            (self.workspace / "vite.config.ts").is_file(),
        ]):
            return "web-dev"

        # Rust
        if (self.workspace / "Cargo.toml").is_file():
            return "adhd-default"  # No rust-specific profile yet

        # Go
        if (self.workspace / "go.mod").is_file():
            return "adhd-default"

        # Generic Python
        if (self.workspace / "setup.py").is_file() or (self.workspace / "pyproject.toml").is_file():
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

        # Ensure workspace directory exists (tests may provide new paths)
        try:
            self.workspace.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path(tempfile.mkdtemp(prefix="dopemux-init-"))
            if fallback != self.workspace:
                console.print(
                    f"[yellow]⚠️ Unable to create workspace at {self.workspace}; "
                    f"using {fallback} instead.[/yellow]"
                )
                self.workspace = fallback
                self.dopemux_dir = self.workspace / ".dopemux"
                self.dopemux_dir.parent.mkdir(parents=True, exist_ok=True)
            else:
                raise

        # Check if already initialized
        if self.dopemux_dir.is_dir() and not force:
            console.logger.info(f"\n[yellow]⚠️  Project already initialized (.dopemux/ exists)[/yellow]")

            if not Confirm.ask("Reinitialize?", default=False):
                console.logger.info("[dim]Cancelled. Use --force to skip confirmation.[/dim]")
                return False

        profiles = self.profile_manager.list_profiles()
        interactive = self._is_interactive()

        # Step 1: Profile selection
        if not profile_name:
            detected = self.detect_project_type()

            if detected:
                console.logger.info(f"\n🔍 [bold]Detected project type:[/bold] {detected}")

                if interactive:
                    if Confirm.ask(f"Use profile '{detected}'?", default=True):
                        profile_name = detected
                    else:
                        profile_name = self._prompt_profile_selection(profiles)
                else:
                    profile_name = detected
            else:
                console.logger.info("\n[dim]Could not auto-detect project type[/dim]")
                if interactive:
                    profile_name = self._prompt_profile_selection(profiles)
                else:
                    if profiles:
                        profile_name = profiles[0].name
                        console.print(
                            f"[dim]Non-interactive mode detected; defaulting to profile '{profile_name}'.[/dim]"
                        )
                    else:
                        profile_name = "adhd-default"

        # Verify profile exists
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            console.logger.info(f"\n[red]❌ Profile not found: {profile_name}[/red]")
            console.logger.info("[dim]Run: dopemux profile list[/dim]")
            return False

        # Step 2: Create .dopemux/ structure
        console.logger.info(f"\n📁 Creating .dopemux/ directory...")
        self.dopemux_dir.mkdir(exist_ok=True)
        (self.dopemux_dir / "databases").mkdir(exist_ok=True)

        # Step 3: Set active profile
        self.profile_manager.set_active_profile(self.workspace, profile_name)
        console.logger.info(f"   Active profile: {profile_name}")

        # Step 4: Create config.yaml (optional project overrides)
        config_file = self.dopemux_dir / "config.yaml"
        if not Path.exists(config_file):
            config_file.write_text("# Project-specific configuration overrides\n# Merged with profile settings\n")
            console.logger.info(f"   Created: .dopemux/config.yaml")

        # Step 5: Summary
        console.logger.info(f"\n✅ [bold green]Initialization complete![/bold green]")
        console.logger.info(f"\n[bold]Next steps:[/bold]")
        console.logger.info(f"  1. Review profile: [cyan]dopemux profile show[/cyan]")
        console.logger.info(f"  2. Start dopemux: [cyan]dopemux start[/cyan]")
        console.logger.info(f"  3. (Optional) Edit: [dim].dopemux/config.yaml[/dim]")

        return True

    def _prompt_profile_selection(self, profiles: Optional[List[DopemuxProfile]] = None) -> str:
        """Prompt user to select a profile."""
        profiles = profiles or self.profile_manager.list_profiles()

        if not profiles:
            console.logger.info("[yellow]No profiles available. Using 'adhd-default'[/yellow]")
            return "adhd-default"

        console.logger.info("\n[bold]Available profiles:[/bold]")
        for i, p in enumerate(profiles, 1):
            console.logger.info(f"  {i}. [cyan]{p.name}[/cyan] - {p.description}")

        choice = Prompt.ask(
            "\nSelect profile",
            choices=[str(i) for i in range(1, len(profiles) + 1)],
            default="1"
        )

        return profiles[int(choice) - 1].name

    @staticmethod
    def _is_interactive() -> bool:
        """Determine if stdin is interactive (TTY)."""
        try:
            stream = click.get_text_stream("stdin")
            return bool(stream and stream.isatty())
        except Exception as e:
            return False
def init_project(workspace: Path, profile: Optional[str], force: bool) -> bool:
    """Run project initialization (called from CLI)."""
    initializer = ProjectInitializer(workspace)
    return initializer.initialize(profile, force)
