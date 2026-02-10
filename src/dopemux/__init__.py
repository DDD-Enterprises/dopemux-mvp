"""
Dopemux: ADHD-optimized development platform that wraps Claude Code.

A Python CLI tool that provides specialized ADHD accommodations for software development,
including context preservation, attention monitoring, and task decomposition.
"""

__version__ = "0.1.0"
__author__ = "Dopemux Team"
__email__ = "team@dopemux.dev"

# Core modules (lightweight)
from . import global_config
from . import workspace_detection

# Profile management
from . import profile_models, profile_parser

__all__ = ["global_config", "workspace_detection", "profile_models", "profile_parser", "__version__"]
