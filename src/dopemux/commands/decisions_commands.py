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
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip

@click.group()
def decisions():
    """
    📊 Decision Governance: Track and analyze cockpit conclusions

    Orchestrates the logging and analysis of ritual decisions within the 
    persistent knowledge graph. Synchronizes ADHD-optimized visualizations 
    with review workflows to ensure high-fidelity cognitive alignment.
    """
    pass


@decisions.group()
def energy():
    """
    ⚡ Vitality Telemetry: Track ritual energy levels

    Synchronizes ADHD-optimized energy tracking rituals. Monitors cognitive 
    vitality patterns throughout the temporal cycle to optimize 
    decision-making timing and ritual efficiency.
    """
    pass


@decisions.group()
def patterns():
    """
    🔍 Cognitive Synthesis: Pattern detection and learning

    Engages the pattern detection engine to synthesize insights from 
    decision history. Automatically clusters ritual tags, identifies 
    sequential chains, and correlates energy telemetry with ritual quality.
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
