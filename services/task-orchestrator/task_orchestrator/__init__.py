# Task-Orchestrator Package

"""
Modular Task-Orchestrator - Intelligent PM automation middleware.

This package provides coordination between Leantime PM interface and AI agents
with implicit automation and ADHD-optimized development workflow orchestration.

Modules:
- config.py: Environment configuration
- models.py: Task status, agent types, and dataclasses
- core.py: Leantime and Redis connections
- adhd/: ADHD monitoring and accommodations
- agents/: AI agent coordination
- sync/: Multi-directional synchronization
- mcp/: MCP tool definitions
"""

from .config import settings

__version__ = "2.0.0"
