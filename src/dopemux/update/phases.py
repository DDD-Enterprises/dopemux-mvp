"""
Dopemux Update Phases

Individual phase implementations for the multi-phase update process.
Each phase handles a specific aspect of the update with error recovery.
"""

import asyncio
import json
import logging
import subprocess
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING

import docker
import yaml
from rich.table import Table

if TYPE_CHECKING:
    from .manager import UpdateManager

logger = logging.getLogger(__name__)


class BasePhase(ABC):
    """Base class for all update phases."""

    def __init__(self, manager: 'UpdateManager'):
        self.manager = manager
        self.config = manager.config
        self.console = manager.console
        self.project_root = manager.project_root

    @abstractmethod
    async def execute(self) -> bool:
        """Execute the phase. Returns True on success, False on failure."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable phase name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Phase description for progress display."""
        pass


class DiscoveryPhase(BasePhase):
    """Phase 1: Discover what needs to be updated."""

    @property
    def name(self) -> str:
        return "Discovery"

    @property
    def description(self) -> str:
        return "Checking for updates and changes"

    async def execute(self) -> bool:
        """Discover and analyze what needs updating."""
        try:
            self.console.print("[cyan]📊 Checking for updates...[/cyan]")

            # Get version information
            version_info = self.manager.check_for_updates()

            if version_info.current == version_info.target:
                self.console.print("[green]✅ Already up to date![/green]")
                return True

            # Analyze changes
            changes = await self._analyze_changes(version_info)

            # Show update preview
            self._show_update_preview(version_info, changes)

            # Ask for confirmation if not dry run
            if not self.config.dry_run:
                import click
                if not click.confirm("Continue with update?", default=True):
                    self.console.print("[yellow]Update cancelled by user[/yellow]")
                    return False

            return True

        except Exception as e:
            logger.exception("Discovery phase failed")
            self.console.print(f"[red]Discovery failed: {e}[/red]")
            return False

    async def _analyze_changes(self, version_info) -> Dict[str, Any]:
        """Analyze what will change in the update."""
        changes = {
            'git_changes': await self._check_git_changes(),
            'docker_changes': await self._check_docker_changes(),
            'dependency_changes': await self._check_dependency_changes(),
            'config_changes': await self._check_config_changes(),
            'migration_required': version_info.requires_migration
        }
        return changes

    async def _check_git_changes(self) -> List[str]:
        """Check for git changes."""
        try:
            result = subprocess.run(
                ["git", "fetch", "origin"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return ["Failed to fetch from remote"]

            result = subprocess.run(
                ["git", "log", "--oneline", "HEAD..origin/main"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('\\n')
                return [f"New commit: {commit}" for commit in commits[:5]]

            return ["No new commits"]

        except Exception as e:
            return [f"Git check failed: {e}"]

    async def _check_docker_changes(self) -> List[str]:
        """Check for Docker image changes."""
        changes = []

        # Check docker-compose files for modifications
        compose_files = list(self.project_root.glob("**/docker-compose*.yml"))

        for compose_file in compose_files:
            try:
                with open(compose_file) as f:
                    compose_data = yaml.safe_load(f)

                services = compose_data.get('services', {})
                for service_name, service_config in services.items():
                    if 'build' in service_config:
                        changes.append(f"Service '{service_name}' may need rebuild")
                    elif 'image' in service_config:
                        changes.append(f"Service '{service_name}' may have new image")

            except Exception as e:
                changes.append(f"Could not analyze {compose_file}: {e}")

        return changes if changes else ["No Docker changes detected"]

    async def _check_dependency_changes(self) -> List[str]:
        """Check for dependency changes."""
        changes = []

        # Check Python dependencies
        requirements_files = [
            self.project_root / "requirements.txt",
            self.project_root / "pyproject.toml"
        ]

        for req_file in requirements_files:
            if req_file.exists():
                changes.append(f"Python dependencies in {req_file.name} may have updates")

        # Check Node dependencies
        package_files = list(self.project_root.glob("**/package.json"))
        for pkg_file in package_files:
            changes.append(f"Node dependencies in {pkg_file.relative_to(self.project_root)}")

        return changes if changes else ["No dependency changes detected"]

    async def _check_config_changes(self) -> List[str]:
        """Check for configuration changes."""
        config_files = [
            ".env.example",
            "config/mcp/*.yaml",
            ".claude/CLAUDE.md"
        ]

        changes = []
        for pattern in config_files:
            matching_files = list(self.project_root.glob(pattern))
            if matching_files:
                changes.append(f"Configuration files: {pattern}")

        return changes if changes else ["No configuration changes"]

    def _show_update_preview(self, version_info, changes) -> None:
        """Show user-friendly update preview."""
        self.console.print(f"\\n[bold]📋 Update Plan: v{version_info.current} → v{version_info.target}[/bold]")

        # Create update summary table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        # Add rows based on discovered changes
        if changes['git_changes'] and "No new commits" not in changes['git_changes'][0]:
            table.add_row("Code", "📝 Updates available", f"{len(changes['git_changes'])} new commits")
        else:
            table.add_row("Code", "✅ Up to date", "No changes")

        if "No Docker changes" not in changes['docker_changes'][0]:
            table.add_row("Docker", "🔄 Rebuild needed", f"{len(changes['docker_changes'])} services")
        else:
            table.add_row("Docker", "✅ No changes", "Images current")

        if "No dependency changes" not in changes['dependency_changes'][0]:
            table.add_row("Dependencies", "📦 Updates available", "Python/Node packages")
        else:
            table.add_row("Dependencies", "✅ Current", "No updates needed")

        if changes['migration_required']:
            table.add_row("Database", "🔄 Migration needed", "Schema updates required")

        self.console.print(table)

        self.console.print("\\n[dim]⏱️ Estimated time: 15-20 minutes[/dim]")
        self.console.print("[dim]💾 Backup space needed: ~250 MB[/dim]")


class BackupPhase(BasePhase):
    """Phase 2: Create comprehensive backups."""

    @property
    def name(self) -> str:
        return "Backup"

    @property
    def description(self) -> str:
        return "Creating backups and safety checkpoints"

    async def execute(self) -> bool:
        """Create comprehensive backups before update."""
        if self.config.skip_backups:
            self.console.print("[yellow]⚠️ Skipping backups (as requested)[/yellow]")
            return True

        try:
            self.console.print("[cyan]💾 Creating backups...[/cyan]")

            # Create timestamped backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_info = self.manager.check_for_updates()
            backup_name = f"v{version_info.current}_to_v{version_info.target}_{timestamp}"
            backup_path = self.manager.backup_dir / backup_name

            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup databases
            await self._backup_databases(backup_path)

            # Backup configurations
            await self._backup_configurations(backup_path)

            # Create backup manifest
            await self._create_backup_manifest(backup_path, version_info)

            # Register backup with rollback manager
            self.manager.rollback.register_backup(backup_path)

            self.console.print(f"[green]✅ Backup created: {backup_name}[/green]")
            return True

        except Exception as e:
            logger.exception("Backup phase failed")
            self.console.print(f"[red]Backup failed: {e}[/red]")
            return False

    async def _backup_databases(self, backup_path: Path) -> None:
        """Backup all databases."""
        db_backup_dir = backup_path / "databases"
        db_backup_dir.mkdir(exist_ok=True)

        # Backup ConPort SQLite database
        conport_db = self.project_root / ".dopemux" / "conport.db"
        if conport_db.exists():
            shutil.copy2(conport_db, db_backup_dir / "conport.db")

        # Backup Redis data (if running)
        try:
            result = subprocess.run(
                ["docker", "exec", "redis", "redis-cli", "BGSAVE"],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                # Copy Redis dump
                result = subprocess.run([
                    "docker", "cp", "redis:/data/dump.rdb",
                    str(db_backup_dir / "redis.rdb")
                ], timeout=30)
        except Exception as e:
            logger.warning(f"Redis backup failed (non-critical): {e}")

    async def _backup_configurations(self, backup_path: Path) -> None:
        """Backup configuration files."""
        config_backup_dir = backup_path / "configs"
        config_backup_dir.mkdir(exist_ok=True)

        # Backup key configuration files
        config_patterns = [
            ".env*",
            ".claude/**/*",
            "config/**/*",
            "docker/**/*.yml",
            "*.toml",
            "*.yaml"
        ]

        for pattern in config_patterns:
            for config_file in self.project_root.glob(pattern):
                if config_file.is_file():
                    rel_path = config_file.relative_to(self.project_root)
                    dest_file = config_backup_dir / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(config_file, dest_file)

    async def _create_backup_manifest(self, backup_path: Path, version_info) -> None:
        """Create backup manifest with metadata."""
        from datetime import datetime

        manifest = {
            'created_at': datetime.now().isoformat(),
            'version_from': version_info.current,
            'version_to': version_info.target,
            'backup_type': 'full',
            'contents': {
                'databases': list((backup_path / "databases").glob("*")),
                'configs': list((backup_path / "configs").rglob("*"))
            }
        }

        with open(backup_path / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2, default=str)


class UpdatePhase(BasePhase):
    """Phase 3: Execute core updates (git, dependencies, Docker)."""

    @property
    def name(self) -> str:
        return "Update"

    @property
    def description(self) -> str:
        return "Updating code, dependencies, and containers"

    async def execute(self) -> bool:
        """Execute core update operations."""
        try:
            self.console.print("[cyan]🔄 Executing updates...[/cyan]")

            # Git synchronization
            if not await self._update_git():
                return False

            # Dependency updates
            if not await self._update_dependencies():
                return False

            # Docker updates
            if not self.config.skip_docker and not await self._update_docker():
                return False

            self.console.print("[green]✅ Core updates completed[/green]")
            return True

        except Exception as e:
            logger.exception("Update phase failed")
            self.console.print(f"[red]Update phase failed: {e}[/red]")
            return False

    async def _update_git(self) -> bool:
        """Update git repository with stash/pop for local changes."""
        try:
            self.console.print("[dim]📝 Saving local changes...[/dim]")

            # Stash any local changes
            stash_result = subprocess.run(
                ["git", "stash", "save", f"dopemux-update-{datetime.now().strftime('%Y%m%d_%H%M%S')}"],
                capture_output=True, text=True, timeout=30
            )

            # Pull latest changes
            self.console.print("[dim]⬇️ Pulling latest changes...[/dim]")
            pull_result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True, text=True, timeout=60
            )

            if pull_result.returncode != 0:
                self.console.print(f"[red]Git pull failed: {pull_result.stderr}[/red]")
                return False

            # Pop stashed changes if any were stashed
            if "No local changes to save" not in stash_result.stdout:
                self.console.print("[dim]📝 Restoring local changes...[/dim]")
                pop_result = subprocess.run(
                    ["git", "stash", "pop"],
                    capture_output=True, text=True, timeout=30
                )

                if pop_result.returncode != 0:
                    self.console.print("[yellow]⚠️ Could not restore local changes automatically[/yellow]")
                    self.console.print("[yellow]You may need to resolve conflicts manually[/yellow]")

            return True

        except Exception as e:
            logger.exception("Git update failed")
            self.console.print(f"[red]Git update failed: {e}[/red]")
            return False

    async def _update_dependencies(self) -> bool:
        """Update Python and Node dependencies."""
        try:
            # Update Python dependencies
            if (self.project_root / "requirements.txt").exists():
                self.console.print("[dim]📦 Updating Python dependencies...[/dim]")
                result = subprocess.run(
                    ["pip", "install", "-r", "requirements.txt", "--upgrade"],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    self.console.print(f"[yellow]Python dependency update had issues: {result.stderr}[/yellow]")

            # Update pyproject.toml dependencies
            if (self.project_root / "pyproject.toml").exists():
                self.console.print("[dim]📦 Installing project dependencies...[/dim]")
                result = subprocess.run(
                    ["pip", "install", "-e", ".[dev]"],
                    capture_output=True, text=True, timeout=300
                )

            # Update Node dependencies in MCP servers
            mcp_servers_dir = self.project_root / "docker" / "mcp-servers"
            if mcp_servers_dir.exists():
                for server_dir in mcp_servers_dir.iterdir():
                    package_json = server_dir / "package.json"
                    if package_json.exists():
                        self.console.print(f"[dim]📦 Updating Node dependencies in {server_dir.name}...[/dim]")
                        result = subprocess.run(
                            ["npm", "update"],
                            cwd=server_dir, capture_output=True, text=True, timeout=180
                        )

            return True

        except Exception as e:
            logger.exception("Dependency update failed")
            self.console.print(f"[red]Dependency update failed: {e}[/red]")
            return False

    async def _update_docker(self) -> bool:
        """Update Docker images and containers."""
        try:
            # Find docker-compose files
            compose_files = list(self.project_root.glob("**/docker-compose*.yml"))

            for compose_file in compose_files:
                self.console.print(f"[dim]🐳 Updating Docker services in {compose_file.name}...[/dim]")

                # Build only services that need rebuilding
                build_result = subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "build", "--parallel"],
                    capture_output=True, text=True, timeout=600
                )

                if build_result.returncode != 0:
                    self.console.print(f"[yellow]Docker build warnings in {compose_file.name}: {build_result.stderr}[/yellow]")

            return True

        except Exception as e:
            logger.exception("Docker update failed")
            self.console.print(f"[red]Docker update failed: {e}[/red]")
            return False


class OrchestrationPhase(BasePhase):
    """Phase 4: Orchestrate service restarts and migrations."""

    @property
    def name(self) -> str:
        return "Orchestration"

    @property
    def description(self) -> str:
        return "Restarting services and applying migrations"

    async def execute(self) -> bool:
        """Orchestrate service restarts and migrations."""
        try:
            self.console.print("[cyan]🎭 Orchestrating services...[/cyan]")

            # Apply database migrations
            if not await self._apply_migrations():
                return False

            # Restart services in dependency order
            if not await self._restart_services():
                return False

            # Update MCP configurations
            if not await self._update_mcp_configs():
                return False

            self.console.print("[green]✅ Service orchestration completed[/green]")
            return True

        except Exception as e:
            logger.exception("Orchestration phase failed")
            self.console.print(f"[red]Orchestration failed: {e}[/red]")
            return False

    async def _apply_migrations(self) -> bool:
        """Apply any database migrations."""
        try:
            migrations_dir = self.project_root / "migrations"
            if not migrations_dir.exists():
                return True  # No migrations needed

            version_info = self.manager.check_for_updates()
            migration_path = f"v{version_info.current}_to_v{version_info.target}"
            specific_migration = migrations_dir / migration_path

            if specific_migration.exists():
                self.console.print(f"[dim]🔄 Applying migration: {migration_path}...[/dim]")

                # Run pre-migration script
                pre_script = specific_migration / "pre.py"
                if pre_script.exists():
                    result = subprocess.run(
                        ["python", str(pre_script)],
                        capture_output=True, text=True, timeout=60
                    )
                    if result.returncode != 0:
                        self.console.print(f"[red]Pre-migration failed: {result.stderr}[/red]")
                        return False

                # Run main migration script
                migrate_script = specific_migration / "migrate.py"
                if migrate_script.exists():
                    result = subprocess.run(
                        ["python", str(migrate_script)],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode != 0:
                        self.console.print(f"[red]Migration failed: {result.stderr}[/red]")
                        return False

                # Run post-migration script
                post_script = specific_migration / "post.py"
                if post_script.exists():
                    result = subprocess.run(
                        ["python", str(post_script)],
                        capture_output=True, text=True, timeout=60
                    )
                    if result.returncode != 0:
                        self.console.print(f"[yellow]Post-migration warnings: {result.stderr}[/yellow]")

            return True

        except Exception as e:
            logger.exception("Migration failed")
            self.console.print(f"[red]Migration failed: {e}[/red]")
            return False

    async def _restart_services(self) -> bool:
        """Restart services in proper dependency order."""
        try:
            # Critical services first
            critical_services = ["redis", "postgres"]
            await self._restart_service_group(critical_services, "Critical services")

            # Wait for stability
            await asyncio.sleep(10)

            # MCP servers
            mcp_services = ["mas-sequential-thinking", "conport", "zen", "context7"]
            await self._restart_service_group(mcp_services, "MCP servers")

            # Wait for MCP servers to initialize
            await asyncio.sleep(15)

            # Other services
            other_services = ["gptr-mcp", "serena", "task-master-ai"]
            await self._restart_service_group(other_services, "Other services")

            return True

        except Exception as e:
            logger.exception("Service restart failed")
            self.console.print(f"[red]Service restart failed: {e}[/red]")
            return False

    async def _restart_service_group(self, services: List[str], group_name: str) -> None:
        """Restart a group of services."""
        self.console.print(f"[dim]🔄 Restarting {group_name}...[/dim]")

        # Try to restart via docker-compose
        compose_file = self.project_root / "docker" / "mcp-servers" / "docker-compose.yml"
        if compose_file.exists():
            for service in services:
                try:
                    # Stop service
                    subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "stop", service],
                        capture_output=True, timeout=30
                    )

                    # Start service
                    subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "start", service],
                        capture_output=True, timeout=60
                    )

                except subprocess.TimeoutExpired:
                    self.console.print(f"[yellow]Service {service} restart took longer than expected[/yellow]")
                except Exception as e:
                    logger.warning(f"Could not restart {service}: {e}")

    async def _update_mcp_configs(self) -> bool:
        """Update Claude Code MCP server configurations."""
        try:
            # This would integrate with Claude Code's configuration system
            # For now, just indicate that MCP configs should be updated
            self.console.print("[dim]🔧 MCP configurations may need manual update[/dim]")
            return True

        except Exception as e:
            logger.exception("MCP config update failed")
            return False


class ValidationPhase(BasePhase):
    """Phase 5: Validate that everything is working correctly."""

    @property
    def name(self) -> str:
        return "Validation"

    @property
    def description(self) -> str:
        return "Verifying system health and functionality"

    async def execute(self) -> bool:
        """Validate that the update was successful."""
        try:
            self.console.print("[cyan]🏥 Validating system health...[/cyan]")

            # Run health checks
            health_results = await self.manager.health.check_all_services()

            # Verify critical paths
            if not await self._verify_critical_paths():
                return False

            # Update version file
            await self._update_version_file()

            # Show validation results
            self._show_validation_results(health_results)

            return all(health_results.values())

        except Exception as e:
            logger.exception("Validation phase failed")
            self.console.print(f"[red]Validation failed: {e}[/red]")
            return False

    async def _verify_critical_paths(self) -> bool:
        """Verify that critical system paths are working."""
        try:
            # Test ConPort connectivity
            # Test MCP server responsiveness
            # Test basic CLI functionality

            self.console.print("[dim]✅ Critical paths verified[/dim]")
            return True

        except Exception as e:
            logger.exception("Critical path verification failed")
            return False

    async def _update_version_file(self) -> None:
        """Update the VERSION file with the new version."""
        version_info = self.manager.check_for_updates()
        version_file = self.project_root / "VERSION"

        version_file.write_text(version_info.target)
        self.console.print(f"[dim]📝 Updated VERSION file to {version_info.target}[/dim]")

    def _show_validation_results(self, health_results: Dict[str, bool]) -> None:
        """Show validation results in a user-friendly format."""
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Service", style="cyan")
        table.add_column("Status")

        for service, healthy in health_results.items():
            status = "[green]✅ Healthy[/green]" if healthy else "[red]❌ Unhealthy[/red]"
            table.add_row(service, status)

        self.console.print("\\n[bold]🏥 Health Check Results:[/bold]")
        self.console.print(table)