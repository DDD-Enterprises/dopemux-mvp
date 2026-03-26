"""Backward-compatible re-export facade.

All functionality has been split into focused modules.
This module re-exports everything for existing callers that do
`from dopemux_pr_merge_specialist import engine` and then `engine.foo()`.
"""

from __future__ import annotations

# Re-export everything for backward compatibility
from .classification import *  # noqa: F401,F403
from .conflict import *  # noqa: F401,F403
from .github_api import GitHubClient, summarize_checks  # noqa: F401
from .merge import *  # noqa: F401,F403
from .plan_builder import *  # noqa: F401,F403
from .preflight import *  # noqa: F401,F403
from .queue import *  # noqa: F401,F403
from .queue_drain import *  # noqa: F401,F403

# Also re-export runtime types tests reference via engine.CommandResult
from .runtime import CommandResult, execute_or_dry_run  # noqa: F401
from .thread_resolution import *  # noqa: F401,F403
from .worktree import *  # noqa: F401,F403
