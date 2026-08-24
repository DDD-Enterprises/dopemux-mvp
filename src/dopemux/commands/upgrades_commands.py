"""
Upgrades Commands
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

@click.group()
def upgrades():
    """
    🧪 Ritual Advancement: Universal Repo-Truth-Extractor commands

    Orchestrates the high-fidelity extraction of repository intelligence.
    This system synchronizes across multiple pipeline versions (v3, v4, v5)
    to harvest codebase patterns, synthesize promptsets, and maintain the
    integrity of the ritual knowledge graph.
    """
    # TP-RTE-TRUTH-R4-002 (F-42): `upgrades` is a deprecated, hidden alias.
    # `rte` is now the canonical definition site for every subcommand
    # attached here. This callback only fires when a subcommand is actually
    # invoked (Click group-callback semantics), so `--help` on the bare
    # group and canonical `rte` invocations never see this warning.
    console.logger.warning(
        "`dopemux upgrades` is a deprecated alias for `dopemux rte`. "
        "Use `dopemux rte <command>` instead."
    )


