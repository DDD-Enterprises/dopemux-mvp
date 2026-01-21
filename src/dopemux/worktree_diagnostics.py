#!/usr/bin/env python3
"""
Worktree Diagnostics System

Comprehensive health check for worktree configuration and workflow.
Provides ADHD-friendly diagnostics with clear actionable fixes.

Key Features:
- One command checks everything
- Clear pass/fail indicators
- Actionable fix suggestions
- Performance metrics
- ADHD-optimized: Progressive disclosure, visual clarity

Target: < 1 second execution for instant feedback
"""

import json

import logging

logger = logging.getLogger(__name__)

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .auto_configurator import WorktreeAutoConfigurator
from .workspace_detection import get_workspace_root, get_workspace_info, validate_workspace
from .worktree_templates import WorktreeTemplateManager

console = Console()


class WorktreeDiagnostics:
    """
    Comprehensive worktree system diagnostics.

    **Check Categories**:
    1. Workspace Detection (Phase 1)
    2. MCP Auto-Configuration (Phase 2)
    3. Template Coverage (Phase 3)
    4. Shell Integration (Phase 3)
    5. Common Issues
    """

    def __init__(self):
        """Initialize diagnostics system."""
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warnings = 0

    def run_all_checks(self, verbose: bool = False) -> bool:
        """
        Run all diagnostic checks.

        Args:
            verbose: Show detailed information

        Returns:
            True if all critical checks passed
        """
        console.logger.info("\n[bold cyan]🏥 Dopemux Worktree Diagnostics[/bold cyan]\n")

        # Phase 1: Workspace Detection
        console.logger.info("[bold]Phase 1: Workspace Detection[/bold]")
        workspace_ok = self._check_workspace_detection(verbose)

        # Phase 2: MCP Auto-Configuration
        console.logger.info("\n[bold]Phase 2: MCP Auto-Configuration[/bold]")
        mcp_ok = self._check_mcp_configuration(verbose)

        # Phase 3: Template Coverage
        console.logger.info("\n[bold]Phase 3: Template Coverage[/bold]")
        template_ok = self._check_template_coverage(verbose)

        # Phase 3: Shell Integration
        console.logger.info("\n[bold]Phase 3: Shell Integration[/bold]")
        shell_ok = self._check_shell_integration(verbose)

        # Summary
        self._print_summary()

        # All critical checks must pass
        return workspace_ok and mcp_ok

    def _check_workspace_detection(self, verbose: bool) -> bool:
        """Check Phase 1: Workspace detection functionality."""
        try:
            workspace = get_workspace_root()
            workspace_info = get_workspace_info(workspace)
            is_valid, error = validate_workspace(workspace)

            if is_valid:
                self._check_pass(f"Workspace detected: {workspace}")

                if verbose:
                    console.logger.info(f"  [dim]Git repo: {workspace_info.get('is_git_repo')}[/dim]")
                    console.logger.info(f"  [dim]Worktree: {workspace_info.get('is_worktree')}[/dim]")
                    console.logger.info(f"  [dim]Method: {workspace_info.get('detection_method')}[/dim]")

                return True
            else:
                self._check_fail(f"Workspace validation failed: {error}")
                return False

        except Exception as e:
            self._check_fail(f"Workspace detection error: {e}")
            return False

            logger.error(f"Error: {e}")
    def _check_mcp_configuration(self, verbose: bool) -> bool:
        """Check Phase 2: MCP auto-configuration status."""
        try:
            auto_config = WorktreeAutoConfigurator()
            status = auto_config.get_status()

            if not status.get("enabled"):
                self._check_warning("Auto-configuration disabled (DOPEMUX_LEGACY_DETECTION=1)")
                return True  # Not a failure, just legacy mode

            if not status.get("config_exists"):
                self._check_fail("~/.claude.json not found")
                console.logger.info("  [yellow]💡 Fix: Create .claude.json or run 'dopemux start'[/yellow]")
                return False

            workspace = Path(status["current_workspace"])
            needs_update = status.get("needs_update")

            if needs_update:
                self._check_warning(f"MCP configuration needs update for {workspace}")
                console.logger.info("  [yellow]💡 Fix: Run 'dopemux start' or 'dwt <branch>' to auto-configure[/yellow]")
            else:
                self._check_pass(f"MCP configuration correct for {workspace}")

            if verbose:
                console.logger.info(f"  [dim]Config path: {status.get('config_path')}[/dim]")

            return True

        except Exception as e:
            self._check_fail(f"MCP configuration check error: {e}")
            return False

            logger.error(f"Error: {e}")
    def _check_template_coverage(self, verbose: bool) -> bool:
        """Check Phase 3: Template file coverage."""
        try:
            template_manager = WorktreeTemplateManager()
            status = template_manager.get_template_status()

            if not status.get("main_repo_found"):
                self._check_warning("Not in git repository (templates not applicable)")
                return True

            coverage = status.get("coverage_percent", 0)
            missing = status.get("missing", [])

            if coverage >= 80:
                self._check_pass(f"Template coverage: {coverage:.1f}%")
            elif coverage >= 50:
                self._check_warning(f"Template coverage: {coverage:.1f}% (recommended: 80%+)")
            else:
                self._check_fail(f"Template coverage: {coverage:.1f}% (low)")

            if missing and verbose:
                console.logger.info(f"  [dim]Missing templates:[/dim]")
                for file in missing[:5]:  # Show first 5
                    console.logger.info(f"    [dim]- {file}[/dim]")
                if len(missing) > 5:
                    console.logger.info(f"    [dim]... and {len(missing) - 5} more[/dim]")

            return True

        except Exception as e:
            self._check_fail(f"Template coverage check error: {e}")
            return False

            logger.error(f"Error: {e}")
    def _check_shell_integration(self, verbose: bool) -> bool:
        """Check Phase 3: Shell integration status."""
        try:
            # Check if dwt function is available
            shell = os.getenv("SHELL", "")
            shell_name = Path(shell).name if shell else "unknown"

            if shell_name not in ["bash", "zsh"]:
                self._check_warning(f"Unsupported shell: {shell_name} (bash/zsh only)")
                return True

            # Check if shell config exists
            home = Path.home()
            if shell_name == "bash":
                shell_config = home / ".bashrc"
            else:
                shell_config = home / ".zshrc"

            if not shell_config.exists():
                self._check_warning(f"Shell config not found: {shell_config}")
                return True

            # Check if dwt function is defined
            with open(shell_config, 'r') as f:
                content = f.read()

            if "# Dopemux Shell Integration" in content:
                self._check_pass("Shell integration installed")

                if verbose:
                    console.logger.info(f"  [dim]Shell: {shell_name}[/dim]")
                    console.logger.info(f"  [dim]Config: {shell_config}[/dim]")

                return True
            else:
                self._check_warning("Shell integration not installed")
                console.logger.info(f"  [yellow]💡 Fix: Run 'dopemux shell-setup {shell_name} >> ~/{shell_config.name} && source ~/{shell_config.name}'[/yellow]")
                return True

        except Exception as e:
            self._check_fail(f"Shell integration check error: {e}")
            return False

            logger.error(f"Error: {e}")
    def _check_pass(self, message: str):
        """Record a passed check."""
        self.checks_passed += 1
        console.logger.info(f"  [green]✅ {message}[/green]")

    def _check_fail(self, message: str):
        """Record a failed check."""
        self.checks_failed += 1
        console.logger.info(f"  [red]❌ {message}[/red]")

    def _check_warning(self, message: str):
        """Record a warning."""
        self.checks_warnings += 1
        console.logger.info(f"  [yellow]⚠️  {message}[/yellow]")

    def _print_summary(self):
        """Print diagnostic summary."""
        console.logger.info("\n[bold]Summary[/bold]")

        total = self.checks_passed + self.checks_failed + self.checks_warnings

        table = Table(show_header=False, box=None)
        table.add_column("Status", style="bold")
        table.add_column("Count")

        table.add_row("✅ Passed", f"[green]{self.checks_passed}/{total}[/green]")

        if self.checks_warnings > 0:
            table.add_row("⚠️  Warnings", f"[yellow]{self.checks_warnings}/{total}[/yellow]")

        if self.checks_failed > 0:
            table.add_row("❌ Failed", f"[red]{self.checks_failed}/{total}[/red]")

        console.logger.info(table)

        # Overall status
        if self.checks_failed == 0:
            if self.checks_warnings == 0:
                console.logger.info("\n[bold green]🎉 All checks passed! Worktree system is healthy.[/bold green]")
            else:
                console.logger.warning("\n[bold yellow]⚠️  Some warnings found. System functional but not optimal.[/bold yellow]")
        else:
            console.logger.error("\n[bold red]❌ Critical issues found. Please address failures above.[/bold red]")


def run_diagnostics(verbose: bool = False) -> bool:
    """
    Run worktree diagnostics.

    Args:
        verbose: Show detailed information

    Returns:
        True if all critical checks passed
    """
    diagnostics = WorktreeDiagnostics()
    return diagnostics.run_all_checks(verbose)
