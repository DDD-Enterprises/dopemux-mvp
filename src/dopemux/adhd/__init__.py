"""
ADHD-specific features and accommodations.

This module provides specialized functionality for developers with ADHD,
including context preservation, attention monitoring, and task decomposition.
"""

from .attention_monitor import AttentionMonitor
from .context_manager import ContextManager
from .task_decomposer import TaskDecomposer

# Note: AttentionManager archived after analysis showed it increased cognitive load
# New approach: Simple, user-controlled ADHD accommodations in MetaMCP server
# Archived code available in: /src/dopemux/adhd/archived/attention_manager.py.archived

__all__ = ["ContextManager", "AttentionMonitor", "TaskDecomposer"]
