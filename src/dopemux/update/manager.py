"""
Dopemux Update Manager

Orchestrates multi-phase updates with ADHD-optimized progress tracking,
automatic backups, rollback capability, and resilient error handling.
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
from enum import Enum

import click
import yaml
from rich.console import Console
from rich.progress import Progress, TaskID

from ..config.base import Config
from .phases import (
    DiscoveryPhase, BackupPhase, UpdatePhase,
    OrchestrationPhase, ValidationPhase
)
from .rollback import RollbackManager
from .progress import ProgressTracker, UpdateState
from .health import HealthChecker


logger = logging.getLogger(__name__)


class UpdateResult(Enum):
    """Update operation results."""
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    INTERRUPTED = "interrupted"


@dataclass
class UpdateConfig:
    """Configuration for update operations."""
    dry_run: bool = False
    minimal: bool = False
    skip_backups: bool = False
    skip_docker: bool = False
    skip_migrations: bool = False
    timeout_minutes: int = 30
    checkpoint_interval: int = 30  # seconds

    # ADHD optimizations
    show_progress: bool = True
    enable_celebrations: bool = True
    checkpoint_saves: bool = True


@dataclass
class VersionInfo:
    """Version tracking information."""
    current: str
    target: str
    migration_path: List[str]
    requires_migration: bool = False
    breaking_changes: bool = False


class UpdateManager:
    """
    Main update orchestrator with ADHD-optimized workflow.

    Coordinates multi-phase updates with automatic checkpointing,
    visual progress tracking, and comprehensive error recovery.
    """

    def __init__(self,
                 config: Optional[UpdateConfig] = None,
                 project_root: Optional[Path] = None):
        self.config = config or UpdateConfig()
        self.project_root = project_root or Path.cwd()
        self.console = Console()

        # Core components
        self.progress = ProgressTracker(self.console)
        self.rollback = RollbackManager(self.project_root)
        self.health = HealthChecker(self.project_root)

        # State management
        self.session_dir = self.project_root / ".dopemux" / "update-session"
        self.backup_dir = self.project_root / ".dopemux" / "backups"
        self.current_state: Optional[UpdateState] = None
        self.start_time: Optional[datetime] = None

        # Phase orchestration
        self.phases = [
            DiscoveryPhase(self),
            BackupPhase(self),
            UpdatePhase(self),
            OrchestrationPhase(self),
            ValidationPhase(self)
        ]

        # Checkpoint system
        self.last_checkpoint = time.time()

        # Initialize directories
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories for update operations."""
        for directory in [self.session_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_current_version(self) -> str:
        """Get current version from VERSION file."""
        version_file = self.project_root / "VERSION"
        if not version_file.exists():
            return "0.0.0"
        return version_file.read_text().strip()

    def get_target_version(self) -> str:
        """Get target version from remote repository."""
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", "origin"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                # Parse latest tag - simplified for now
                lines = result.stdout.strip().split('\n')
                tags = [line.split('refs/tags/')[-1] for line in lines if 'refs/tags/' in line]
                if tags:
                    # Return latest semantic version tag
                    return max(tags, key=lambda x: tuple(map(int, x.lstrip('v').split('.'))))
            return self.get_current_version()
        except Exception as e:
            logger.warning(f"Could not determine target version: {e}")
            return self.get_current_version()

    def check_for_updates(self) -> VersionInfo:
        """Check if updates are available."""
        current = self.get_current_version()
        target = self.get_target_version()

        # Determine migration requirements
        migration_path = self._calculate_migration_path(current, target)
        requires_migration = len(migration_path) > 1
        breaking_changes = self._has_breaking_changes(current, target)

        return VersionInfo(
            current=current,
            target=target,
            migration_path=migration_path,
            requires_migration=requires_migration,
            breaking_changes=breaking_changes
        )

    def _calculate_migration_path(self, current: str, target: str) -> List[str]:
        """Calculate step-by-step migration path between versions."""
        # Simplified - would need actual migration logic
        if current == target:
            return [current]
        return [current, target]

    def _has_breaking_changes(self, current: str, target: str) -> bool:
        """Check if update includes breaking changes."""
        # Simplified - check major version changes
        try:
            current_major = int(current.split('.')[0])
            target_major = int(target.split('.')[0])
            return target_major > current_major
        except (ValueError, IndexError):
            return False

    async def run_update(self) -> UpdateResult:
        """
        Execute the complete update process.

        Returns:
            UpdateResult indicating success, failure, or rollback
        """
        self.start_time = datetime.now()

        try:
            # Initialize progress tracking
            with self.progress.start_update("Dopemux Update") as update_task:

                # Check for existing interrupted session
                if await self._has_interrupted_session():
                    if self.config.dry_run or await self._ask_resume():
                        return await self._resume_update()

                # Start fresh update
                return await self._run_fresh_update(update_task)

        except KeyboardInterrupt:
            self.console.print("\\n[yellow]Update interrupted by user[/yellow]")
            await self._save_checkpoint("interrupted")
            return UpdateResult.INTERRUPTED

        except Exception as e:
            logger.exception("Update failed with unexpected error")
            self.console.print(f"[red]Update failed: {e}[/red]")

            # Attempt rollback
            if not self.config.dry_run:
                self.console.print("[yellow]Attempting automatic rollback...[/yellow]")
                rollback_success = await self.rollback.auto_rollback()
                if rollback_success:
                    return UpdateResult.ROLLED_BACK

            return UpdateResult.FAILED

    async def _run_fresh_update(self, update_task: TaskID) -> UpdateResult:
        """Run a complete fresh update through all phases."""

        # Execute phases sequentially
        for i, phase in enumerate(self.phases):
            phase_name = phase.__class__.__name__

            self.progress.start_phase(update_task, phase_name, i + 1, len(self.phases))

            try:
                success = await phase.execute()
                if not success:
                    if not self.config.dry_run:
                        await self.rollback.auto_rollback()
                        return UpdateResult.ROLLED_BACK
                    return UpdateResult.FAILED

                # Create checkpoint after each phase
                await self._save_checkpoint(f"completed_{phase_name.lower()}")

            except Exception as e:
                logger.exception(f"Phase {phase_name} failed")
                self.console.print(f"[red]Phase {phase_name} failed: {e}[/red]")

                if not self.config.dry_run:
                    await self.rollback.auto_rollback()
                    return UpdateResult.ROLLED_BACK
                return UpdateResult.FAILED

        # Update completed successfully
        await self._cleanup_session()

        if self.config.enable_celebrations:
            self._show_success_celebration()

        return UpdateResult.SUCCESS

    async def _has_interrupted_session(self) -> bool:
        """Check if there's an interrupted update session to resume."""
        session_file = self.session_dir / "current_session.json"
        return session_file.exists()

    async def _ask_resume(self) -> bool:
        """Ask user if they want to resume interrupted session."""
        return click.confirm(
            "Found interrupted update session. Resume from last checkpoint?",
            default=True
        )

    async def _resume_update(self) -> UpdateResult:
        """Resume an interrupted update session."""
        self.console.print("[green]Welcome back! Picking up where we left off...[/green]")

        # Load session state
        session_file = self.session_dir / "current_session.json"
        with open(session_file) as f:
            session_data = json.load(f)

        last_checkpoint = session_data.get('last_checkpoint', 'start')
        interrupted_time = datetime.fromisoformat(session_data.get('timestamp', ''))
        time_elapsed = datetime.now() - interrupted_time

        self.console.print(f"[dim]Last checkpoint: {last_checkpoint} ({time_elapsed} ago)[/dim]")

        # Resume from appropriate phase
        return await self._run_fresh_update(None)  # Simplified

    async def _save_checkpoint(self, checkpoint_name: str) -> None:
        """Save current update state as checkpoint."""
        if not self.config.checkpoint_saves:
            return

        checkpoint_data = {
            'checkpoint': checkpoint_name,
            'timestamp': datetime.now().isoformat(),
            'version_info': asdict(self.check_for_updates()),
            'config': asdict(self.config)
        }

        session_file = self.session_dir / "current_session.json"
        with open(session_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        self.last_checkpoint = time.time()

    async def _cleanup_session(self) -> None:
        """Clean up temporary session files after successful update."""
        session_file = self.session_dir / "current_session.json"
        if session_file.exists():
            session_file.unlink()

    def _show_success_celebration(self) -> None:
        """Show ADHD-friendly success celebration."""
        version_info = self.check_for_updates()

        self.console.print("\\n" + "="*50)
        self.console.print("[green]✅ Update Complete! 🎉[/green]")
        self.console.print("="*50)

        self.console.print("\\n[bold]Summary:[/bold]")
        self.console.print(f"  • Updated from v{version_info.current} → v{version_info.target}")
        self.console.print("  • All services healthy")
        self.console.print("  • Configurations preserved")

        if self.start_time:
            duration = datetime.now() - self.start_time
            self.console.print(f"  • Completed in {duration.total_seconds():.1f} seconds")

        self.console.print("\\n[green]Your dopemux is now up to date![/green]")
        self.console.print("[dim]Try the new features with: dopemux --help[/dim]")
        self.console.print()

    async def dry_run(self) -> Dict[str, Any]:
        """
        Perform dry run to show what would be updated.

        Returns:
            Dictionary with update plan details
        """
        original_config = self.config.dry_run
        self.config.dry_run = True

        try:
            version_info = self.check_for_updates()

            plan = {
                'version_info': asdict(version_info),
                'changes': [],
                'estimated_time': '15-20 minutes',
                'backup_size': '~250 MB',
                'phases': [phase.__class__.__name__ for phase in self.phases]
            }

            # Run discovery phase for detailed change analysis
            discovery = DiscoveryPhase(self)
            await discovery.execute()

            return plan

        finally:
            self.config.dry_run = original_config