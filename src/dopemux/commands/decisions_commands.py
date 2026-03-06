"""
Decisions Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
def decisions():
    """
    📊 Decision tracking and analytics

    Manage and analyze decisions logged in ConPort with ADHD-optimized
    visualizations and review workflows.

    \b
    Quick Win Commands:
        review    - Review decisions pending attention
        stats     - Show decision statistics with charts
        energy    - Energy level tracking commands

    Part of ConPort Enhancement roadmap (Phase 1-5).
    """
    pass


@decisions.group()
def energy():
    """
    ⚡ Energy level tracking (ADHD optimization)

    Track your energy levels throughout the day to discover patterns
    and optimize decision-making timing.
    """
    pass


@decisions.group()
def patterns():
    """
    🔍 Pattern detection and learning (Phase 3)

    Auto-detect decision patterns from history:
    - Tag clustering (co-occurring tags)
    - Decision chains (sequential patterns)
    - Timing patterns (time-of-day, duration)
    - Energy correlation (energy vs quality)
    """
    pass


# Import and register decision commands
try:
    from .commands.decisions_commands import (
        review_decisions,
        decision_stats,
        log_energy,
        energy_status,
        show_decision,
        list_decisions,
        energy_analytics,
        graph_decision,
        update_outcome,
        enhanced_stats,
        query_decisions,
        pattern_tags
    )

    # Decision management commands
    decisions.add_command(review_decisions, "review")
    decisions.add_command(decision_stats, "stats")
    decisions.add_command(show_decision, "show")
    decisions.add_command(list_decisions, "list")
    decisions.add_command(graph_decision, "graph")
    decisions.add_command(update_outcome, "update-outcome")
    decisions.add_command(enhanced_stats, "stats-enhanced")
    decisions.add_command(query_decisions, "query")

    # Energy tracking commands
    energy.add_command(log_energy, "log")
    energy.add_command(energy_status, "status")
    energy.add_command(energy_analytics, "analytics")

    # Pattern detection commands (Phase 3)
    patterns.add_command(pattern_tags, "tags")

except ImportError as e:
    # Graceful degradation if dependencies not installed
    pass  # Commands won't be available but CLI still works




# ============================================================================
# Development Mode Commands (Contributor Support)
# ============================================================================

