"""
Update migration compatibility helpers.

Historically referenced as ``dopemux.migration`` in execution packets.
This module wraps update-manager version and migration inspection logic.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .update import UpdateConfig, UpdateManager


@dataclass
class MigrationPlan:
    """Summary of update migration requirements."""

    current: str
    target: str
    path: List[str]
    requires_migration: bool
    breaking_changes: bool


def inspect_migration_plan(
    project_root: Optional[Path] = None,
    manager: Optional[UpdateManager] = None,
) -> MigrationPlan:
    """
    Inspect current->target version migration requirements.
    """
    runtime_manager = manager or UpdateManager(project_root=project_root)
    version_info = runtime_manager.check_for_updates()
    return MigrationPlan(
        current=version_info.current,
        target=version_info.target,
        path=list(version_info.migration_path),
        requires_migration=bool(version_info.requires_migration),
        breaking_changes=bool(version_info.breaking_changes),
    )


def migration_required(
    project_root: Optional[Path] = None,
    manager: Optional[UpdateManager] = None,
) -> bool:
    """Return True when an update path requires migration steps."""
    return inspect_migration_plan(project_root=project_root, manager=manager).requires_migration


def create_dry_run_update_config(timeout_minutes: int = 30) -> UpdateConfig:
    """Build a dry-run-safe update config for planning and validation checks."""
    return UpdateConfig(dry_run=True, timeout_minutes=timeout_minutes)


def format_migration_summary(plan: MigrationPlan) -> str:
    """Render concise human-readable migration summary."""
    migration_label = "required" if plan.requires_migration else "not-required"
    breaking_label = "yes" if plan.breaking_changes else "no"
    path_label = " -> ".join(plan.path)
    return (
        f"current={plan.current} target={plan.target} "
        f"migration={migration_label} breaking={breaking_label} path={path_label}"
    )

