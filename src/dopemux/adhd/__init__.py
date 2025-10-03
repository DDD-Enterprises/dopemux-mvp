"""
ADHD-specific features and accommodations.

This module provides specialized functionality for developers with ADHD,
including context preservation, attention monitoring, and task decomposition.
"""

from .attention_monitor import AttentionMonitor
from .context_manager import ContextManager
# task_decomposer removed - replaced by ConPort progress_entry + services/adhd_engine
# See Decision #152 and docs/90-adr/ADR-XXXX-path-c-migration.md

# Note: AttentionManager archived after analysis showed it increased cognitive load
# New approach: Simple, user-controlled ADHD accommodations in MetaMCP server
# Archived code available in: /src/dopemux/adhd/archived/attention_manager.py.archived

__all__ = ["ContextManager", "AttentionMonitor", "TaskDecomposer"]
