"""
Claude configuration manager facade for profile switching workflows.
"""

from pathlib import Path
from typing import Optional, Tuple

from .claude_config import ClaudeConfig
from .profile_manager import DopemuxProfile


class ClaudeProfileManager:
    """Apply and rollback Claude profile configuration."""

    def __init__(self, config: Optional[ClaudeConfig] = None):
        self.config = config or ClaudeConfig()

    def apply_profile(self, profile: DopemuxProfile) -> Tuple[bool, Optional[Path]]:
        """Apply profile to Claude settings and return backup path."""
        applied, backup_path = self.config.apply_profile(
            profile,
            create_backup=True,
            dry_run=False,
            return_backup_path=True,
        )
        return applied, backup_path

    def rollback(self, backup_path: Optional[Path]) -> bool:
        """Rollback Claude settings to a prior backup path."""
        if backup_path is None:
            return False
        self.config.rollback_to_backup(backup_path)
        return True

