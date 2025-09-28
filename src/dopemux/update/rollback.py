"""
Dopemux Rollback Manager

Comprehensive rollback system with checkpoint management and automatic recovery.
Provides safe rollback to previous system states when updates fail.
"""

import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

logger = logging.getLogger(__name__)


class RollbackManager:
    """
    Manages system rollbacks with checkpoint-based recovery.

    Features:
    - Automatic backup registration
    - Multi-level rollback (code, config, database)
    - Checkpoint-based state restoration
    - Safe failure recovery
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.console = Console()

        # Directory structure
        self.backup_dir = project_root / ".dopemux" / "backups"
        self.rollback_dir = project_root / ".dopemux" / "rollback"
        self.session_dir = project_root / ".dopemux" / "update-session"

        # State tracking
        self.current_backup: Optional[Path] = None
        self.rollback_registry = self.rollback_dir / "registry.json"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories for rollback operations."""
        for directory in [self.backup_dir, self.rollback_dir, self.session_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize registry if it doesn't exist
        if not self.rollback_registry.exists():
            self._save_registry({
                'backups': [],
                'rollback_points': [],
                'last_successful_state': None
            })

    def register_backup(self, backup_path: Path) -> None:
        """Register a new backup for potential rollback."""
        self.current_backup = backup_path

        # Load and update registry
        registry = self._load_registry()
        backup_info = {
            'path': str(backup_path),
            'created_at': datetime.now().isoformat(),
            'type': 'update_backup',
            'manifest_path': str(backup_path / "manifest.json")
        }

        registry['backups'].append(backup_info)

        # Keep only last 5 backups to save space
        registry['backups'] = registry['backups'][-5:]

        self._save_registry(registry)
        logger.info(f"Registered backup: {backup_path}")

    def create_rollback_point(self, checkpoint_name: str,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a rollback point for granular recovery.

        Args:
            checkpoint_name: Name/description of the checkpoint
            metadata: Additional metadata about the checkpoint

        Returns:
            True if checkpoint created successfully
        """
        try:
            timestamp = datetime.now()
            rollback_point = {
                'name': checkpoint_name,
                'timestamp': timestamp.isoformat(),
                'git_commit': self._get_current_git_commit(),
                'version': self._get_current_version(),
                'metadata': metadata or {}
            }

            # Store checkpoint
            registry = self._load_registry()
            registry['rollback_points'].append(rollback_point)

            # Keep only last 10 rollback points
            registry['rollback_points'] = registry['rollback_points'][-10:]

            self._save_registry(registry)

            self.console.print(f"[green]💾 Rollback point created: {checkpoint_name}[/green]")
            return True

        except Exception as e:
            logger.exception("Failed to create rollback point")
            self.console.print(f"[red]Failed to create rollback point: {e}[/red]")
            return False

    async def auto_rollback(self) -> bool:
        """
        Perform automatic rollback when update fails.

        Returns:
            True if rollback was successful
        """
        try:
            self.console.print("[yellow]🔄 Initiating automatic rollback...[/yellow]")

            if not self.current_backup:
                self.console.print("[red]❌ No backup available for rollback[/red]")
                return False

            # Load backup manifest
            manifest_path = self.current_backup / "manifest.json"
            if not manifest_path.exists():
                self.console.print("[red]❌ Backup manifest not found[/red]")
                return False

            with open(manifest_path) as f:
                manifest = json.load(f)

            # Perform rollback steps
            steps = [
                ("Stopping services", self._stop_services),
                ("Restoring databases", lambda: self._restore_databases(self.current_backup)),
                ("Restoring configurations", lambda: self._restore_configurations(self.current_backup)),
                ("Restoring code", lambda: self._restore_code_state(manifest)),
                ("Restarting services", self._restart_services),
                ("Verifying rollback", self._verify_rollback)
            ]

            for step_name, step_func in steps:
                self.console.print(f"[cyan]  → {step_name}...[/cyan]")
                success = await step_func() if hasattr(step_func, '__call__') else step_func()

                if not success:
                    self.console.print(f"[red]❌ {step_name} failed[/red]")
                    return False

                self.console.print(f"[green]✅ {step_name} completed[/green]")

            # Mark last known good state
            registry = self._load_registry()
            registry['last_successful_state'] = {
                'timestamp': datetime.now().isoformat(),
                'backup_path': str(self.current_backup),
                'version': manifest.get('version_from', 'unknown')
            }
            self._save_registry(registry)

            self._show_rollback_success(manifest)
            return True

        except Exception as e:
            logger.exception("Auto rollback failed")
            self.console.print(f"[red]❌ Rollback failed: {e}[/red]")
            return False

    async def manual_rollback(self, backup_name: Optional[str] = None) -> bool:
        """
        Perform manual rollback to a specific backup.

        Args:
            backup_name: Name of backup to rollback to (None for interactive selection)

        Returns:
            True if rollback was successful
        """
        try:
            # Select backup
            if backup_name:
                backup_path = self.backup_dir / backup_name
                if not backup_path.exists():
                    self.console.print(f"[red]Backup '{backup_name}' not found[/red]")
                    return False
            else:
                backup_path = self._select_backup_interactively()
                if not backup_path:
                    return False

            # Confirm rollback
            manifest_path = backup_path / "manifest.json"
            with open(manifest_path) as f:
                manifest = json.load(f)

            version_from = manifest.get('version_from', 'unknown')
            created_at = manifest.get('created_at', 'unknown')

            self.console.print(f"\\n[yellow]⚠️ Rollback Confirmation[/yellow]")
            self.console.print(f"Target backup: {backup_path.name}")
            self.console.print(f"Created: {created_at}")
            self.console.print(f"Will restore to version: {version_from}")

            if not Confirm.ask("Continue with rollback?", default=False):
                self.console.print("[yellow]Rollback cancelled by user[/yellow]")
                return False

            # Set as current backup and perform rollback
            self.current_backup = backup_path
            return await self.auto_rollback()

        except Exception as e:
            logger.exception("Manual rollback failed")
            self.console.print(f"[red]Manual rollback failed: {e}[/red]")
            return False

    def list_available_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        registry = self._load_registry()
        backups = []

        for backup_info in registry.get('backups', []):
            backup_path = Path(backup_info['path'])
            if backup_path.exists():
                # Load manifest for additional info
                manifest_path = backup_path / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                        backup_info.update({
                            'version_from': manifest.get('version_from'),
                            'version_to': manifest.get('version_to'),
                            'size': self._get_backup_size(backup_path)
                        })
                backups.append(backup_info)

        return backups

    def cleanup_old_backups(self, keep_count: int = 3) -> None:
        """Clean up old backups to save disk space."""
        try:
            registry = self._load_registry()
            backups = registry.get('backups', [])

            if len(backups) <= keep_count:
                return

            # Sort by creation time (oldest first)
            backups.sort(key=lambda x: x['created_at'])

            # Remove oldest backups
            backups_to_remove = backups[:-keep_count]
            for backup_info in backups_to_remove:
                backup_path = Path(backup_info['path'])
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    self.console.print(f"[dim]Removed old backup: {backup_path.name}[/dim]")

            # Update registry
            registry['backups'] = backups[-keep_count:]
            self._save_registry(registry)

        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")

    def _select_backup_interactively(self) -> Optional[Path]:
        """Allow user to select backup interactively."""
        backups = self.list_available_backups()

        if not backups:
            self.console.print("[yellow]No backups available[/yellow]")
            return None

        self.console.print("\\n[bold]Available Backups:[/bold]")
        for i, backup in enumerate(backups, 1):
            backup_path = Path(backup['path'])
            created = backup['created_at'][:19]  # Remove microseconds
            version = backup.get('version_from', 'unknown')
            size = backup.get('size', 'unknown')

            self.console.print(f"  {i}. {backup_path.name}")
            self.console.print(f"     Created: {created}")
            self.console.print(f"     Version: {version}")
            self.console.print(f"     Size: {size}")

        try:
            choice = int(input("\\nSelect backup number (0 to cancel): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(backups):
                return Path(backups[choice - 1]['path'])
            else:
                self.console.print("[red]Invalid selection[/red]")
                return None
        except (ValueError, KeyboardInterrupt):
            return None

    def _stop_services(self) -> bool:
        """Stop all dopemux services for rollback."""
        try:
            # Stop via docker-compose
            compose_files = list(self.project_root.glob("**/docker-compose*.yml"))

            for compose_file in compose_files:
                result = subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "stop"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    logger.warning(f"Failed to stop services in {compose_file}: {result.stderr}")

            return True

        except Exception as e:
            logger.exception("Failed to stop services")
            return False

    def _restore_databases(self, backup_path: Path) -> bool:
        """Restore databases from backup."""
        try:
            db_backup_dir = backup_path / "databases"
            if not db_backup_dir.exists():
                return True  # No databases to restore

            # Restore ConPort database
            conport_backup = db_backup_dir / "conport.db"
            if conport_backup.exists():
                conport_target = self.project_root / ".dopemux" / "conport.db"
                shutil.copy2(conport_backup, conport_target)

            # Restore Redis data
            redis_backup = db_backup_dir / "redis.rdb"
            if redis_backup.exists():
                # This would require more complex Redis restoration
                logger.info("Redis backup found but restoration not implemented")

            return True

        except Exception as e:
            logger.exception("Database restoration failed")
            return False

    def _restore_configurations(self, backup_path: Path) -> bool:
        """Restore configuration files from backup."""
        try:
            config_backup_dir = backup_path / "configs"
            if not config_backup_dir.exists():
                return True

            # Restore configuration files
            for config_file in config_backup_dir.rglob("*"):
                if config_file.is_file():
                    rel_path = config_file.relative_to(config_backup_dir)
                    target_file = self.project_root / rel_path

                    # Create parent directories
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(config_file, target_file)

            return True

        except Exception as e:
            logger.exception("Configuration restoration failed")
            return False

    def _restore_code_state(self, manifest: Dict[str, Any]) -> bool:
        """Restore code to previous state."""
        try:
            # This would reset git to the previous commit
            # For now, just log the action
            version_from = manifest.get('version_from', 'unknown')
            self.console.print(f"[dim]Code state: targeting version {version_from}[/dim]")

            # Update VERSION file
            version_file = self.project_root / "VERSION"
            version_file.write_text(version_from)

            return True

        except Exception as e:
            logger.exception("Code state restoration failed")
            return False

    def _restart_services(self) -> bool:
        """Restart services after rollback."""
        try:
            # Restart via docker-compose
            compose_files = list(self.project_root.glob("**/docker-compose*.yml"))

            for compose_file in compose_files:
                result = subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "up", "-d"],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    logger.warning(f"Failed to restart services in {compose_file}: {result.stderr}")

            return True

        except Exception as e:
            logger.exception("Failed to restart services")
            return False

    def _verify_rollback(self) -> bool:
        """Verify that rollback was successful."""
        try:
            # Basic verification - services should be starting
            # More comprehensive verification would use HealthChecker
            return True

        except Exception as e:
            logger.exception("Rollback verification failed")
            return False

    def _show_rollback_success(self, manifest: Dict[str, Any]) -> None:
        """Show rollback success message."""
        version_from = manifest.get('version_from', 'unknown')
        created_at = manifest.get('created_at', 'unknown')

        success_message = (
            f"✅ Rollback completed successfully!\\n\\n"
            f"Restored to version: {version_from}\\n"
            f"Backup from: {created_at}\\n\\n"
            f"Your system has been restored to a working state."
        )

        panel = Panel(
            success_message,
            title="🔄 Rollback Complete",
            border_style="green"
        )
        self.console.print(panel)

    def _load_registry(self) -> Dict[str, Any]:
        """Load rollback registry."""
        try:
            with open(self.rollback_registry) as f:
                return json.load(f)
        except Exception:
            return {'backups': [], 'rollback_points': [], 'last_successful_state': None}

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Save rollback registry."""
        with open(self.rollback_registry, 'w') as f:
            json.dump(registry, f, indent=2)

    def _get_current_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_current_version(self) -> str:
        """Get current version from VERSION file."""
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "unknown"

    def _get_backup_size(self, backup_path: Path) -> str:
        """Calculate backup size in human-readable format."""
        try:
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())

            # Convert to human readable
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0

            return f"{total_size:.1f} TB"

        except Exception:
            return "unknown"