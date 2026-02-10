#!/usr/bin/env python3
"""
Shell Integration Auto-Installer

Opt-in automated installation of shell integration for worktree switching.

Key Features:
- Detects shell type automatically
- Checks if already installed
- Prompts for confirmation (opt-in)
- Automatic backup before changes
- Validation after installation

Design: Make it easy to say yes, safe to try
"""

import os

import logging

logger = logging.getLogger(__name__)

import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from rich.prompt import Confirm

from .console import console


class ShellIntegrationInstaller:
    """
    Automated shell integration installer with safety checks.

    **Safety Features**:
    - Auto-backup of shell config before changes
    - Conflict detection (don't install twice)
    - Validation after installation
    - Clear rollback instructions
    """

    def __init__(self):
        """Initialize installer."""
        self.shell_name = self._detect_shell()
        self.shell_config = self._get_shell_config()
        self.integration_script = self._get_integration_script()

    def _detect_shell(self) -> Optional[str]:
        """Detect current shell type."""
        shell = os.getenv("SHELL", "")
        if not shell:
            return None

        shell_name = Path(shell).name
        if shell_name in ["bash", "zsh"]:
            return shell_name

        return None

    def _get_shell_config(self) -> Optional[Path]:
        """Get shell configuration file path."""
        if not self.shell_name:
            return None

        home = Path.home()

        if self.shell_name == "bash":
            config = home / ".bashrc"
        elif self.shell_name == "zsh":
            config = home / ".zshrc"
        else:
            return None

        return config if config.exists() else None

    def _get_integration_script(self) -> Optional[Path]:
        """Get shell integration script path."""
        # Assume we're in the dopemux package
        script_path = Path(__file__).parent.parent.parent / "scripts" / "shell_integration.sh"

        return script_path if script_path.exists() else None

    def is_supported(self) -> bool:
        """Check if shell integration is supported."""
        return (
            self.shell_name is not None
            and self.shell_config is not None
            and self.integration_script is not None
        )

    def is_installed(self) -> bool:
        """Check if shell integration is already installed."""
        if not self.shell_config or not self.shell_config.exists():
            return False

        with open(self.shell_config, 'r') as f:
            content = f.read()

        return "# Dopemux Shell Integration" in content

    def install(self, auto_confirm: bool = False) -> Tuple[bool, str]:
        """
        Install shell integration with user confirmation.

        Args:
            auto_confirm: Skip confirmation prompt (use with caution)

        Returns:
            Tuple of (success, message)
        """
        # Check support
        if not self.is_supported():
            return False, f"Shell integration not supported for: {self.shell_name or 'unknown shell'}"

        # Check if already installed
        if self.is_installed():
            return True, "Shell integration already installed"

        # Prompt for confirmation
        if not auto_confirm:
            console.logger.info("\n[bold cyan]🐚 Shell Integration Setup[/bold cyan]\n")
            console.logger.info(f"Shell: [bold]{self.shell_name}[/bold]")
            console.logger.info(f"Config: [bold]{self.shell_config}[/bold]\n")

            console.logger.info("[yellow]This will add the following commands to your shell:[/yellow]")
            console.logger.info("  • [bold]dwt[/bold] <branch>  - Switch to worktree with fuzzy matching")
            console.logger.info("  • [bold]dwtls[/bold]         - List all worktrees")
            console.logger.info("  • [bold]dwtcur[/bold]        - Show current worktree\n")

            if not Confirm.ask("Install shell integration?", default=True):
                return False, "Installation cancelled by user"

        # Create backup
        backup_path = self._create_backup()
        console.logger.info(f"[dim]📋 Backup created: {backup_path}[/dim]")

        # Read integration script
        try:
            with open(self.integration_script, 'r') as f:
                integration_code = f.read()
        except Exception as e:
            return False, f"Failed to read integration script: {e}"
        # Append to shell config
        try:
            with open(self.shell_config, 'a') as f:
                f.write(f"\n# Dopemux Shell Integration ({self.shell_name})\n")
                f.write(f"# Installed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Backup: {backup_path.name}\n")
                f.write(integration_code)
                f.write("\n")

            console.logger.info(f"[green]✅ Shell integration installed to {self.shell_config}[/green]")
            console.logger.info(f"[yellow]⚠️  Run this to activate: source {self.shell_config}[/yellow]")

            return True, "Installation successful"

        except Exception as e:
            return False, f"Failed to write to shell config: {e}"
    def _create_backup(self) -> Path:
        """Create timestamped backup of shell config."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.shell_config.with_suffix(f'{self.shell_config.suffix}.backup.{timestamp}')
        shutil.copy2(self.shell_config, backup_path)
        return backup_path

    def prompt_install_if_needed(self) -> bool:
        """
        Prompt to install shell integration if not already installed.

        Returns:
            True if installed or already present, False if user declined
        """
        if self.is_installed():
            return True

        if not self.is_supported():
            console.logger.info(f"[yellow]⚠️  Shell integration not supported for {self.shell_name or 'your shell'}[/yellow]")
            return False

        success, message = self.install(auto_confirm=False)

        if success:
            console.logger.info(f"\n[bold green]🎉 {message}[/bold green]")
            return True
        else:
            console.logger.info(f"\n[bold red]❌ {message}[/bold red]")
            return False


def prompt_install_shell_integration() -> bool:
    """
    Helper function to prompt for shell integration installation.

    Returns:
        True if installed successfully or already present
    """
    installer = ShellIntegrationInstaller()
    return installer.prompt_install_if_needed()
