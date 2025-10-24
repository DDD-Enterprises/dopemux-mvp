"""
Dopemux Infrastructure Agents

7 infrastructure agents that provide ADHD-optimized support for development workflows.

Agents:
- MemoryAgent: Context preservation and auto-save (WEEK 1 - COMPLETE)
- CognitiveGuardian: ADHD support and break reminders (WEEK 3-4 - COMPLETE)
- TwoPlaneOrchestrator: Cross-plane coordination (WEEK 6)
- TaskDecomposer: ADHD-optimized task planning (WEEK 9)
- DopemuxEnforcer: Architectural compliance validation (WEEK 7)
- ToolOrchestrator: Intelligent MCP selection (WEEK 8)
- WorkflowCoordinator: Multi-step workflow orchestration (WEEK 10)

Version: 1.0.0
Status: Phase 1 - MemoryAgent & CognitiveGuardian complete (2/7 agents)
Progress: Weeks 1-4 complete (25% of 16-week plan)
"""

from .memory_agent import MemoryAgent, SessionState
from .cognitive_guardian import (
    CognitiveGuardian,
    AttentionState,
    EnergyLevel,
    UserState,
    BreakReminder
)

__all__ = [
    "MemoryAgent",
    "SessionState",
    "CognitiveGuardian",
    "AttentionState",
    "EnergyLevel",
    "UserState",
    "BreakReminder"
]
