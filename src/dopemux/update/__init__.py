"""
Dopemux Update System

ADHD-optimized update orchestration for complex multi-service environments.
Provides seamless upgrades with backup, rollback, and progress tracking.
"""

from .manager import UpdateManager, UpdateConfig
from .phases import UpdatePhase
from .rollback import RollbackManager
from .progress import ProgressTracker

__all__ = ['UpdateManager', 'UpdateConfig', 'UpdatePhase', 'RollbackManager', 'ProgressTracker']