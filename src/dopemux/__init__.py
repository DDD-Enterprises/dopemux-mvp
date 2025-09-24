"""
Dopemux: ADHD-optimized development platform that wraps Claude Code.

A Python CLI tool that provides specialized ADHD accommodations for software development,
including context preservation, attention monitoring, and task decomposition.
"""

__version__ = "0.1.0"
__author__ = "Dopemux Team"
__email__ = "team@dopemux.dev"

# Core modules
from . import cli, config

__all__ = ["cli", "config", "__version__"]
