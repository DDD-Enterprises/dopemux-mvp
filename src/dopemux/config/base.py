"""
Base configuration classes for Dopemux.

Simple configuration base classes used by various Dopemux subsystems.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class Config:
    """Base configuration class for Dopemux components."""

    project_root: Optional[Path] = None
    debug: bool = False
    log_level: str = "INFO"

    def __post_init__(self):
        if self.project_root is None:
            self.project_root = Path.cwd()
        elif isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'project_root': str(self.project_root),
            'debug': self.debug,
            'log_level': self.log_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        return cls(
            project_root=Path(data.get('project_root', Path.cwd())),
            debug=data.get('debug', False),
            log_level=data.get('log_level', 'INFO')
        )