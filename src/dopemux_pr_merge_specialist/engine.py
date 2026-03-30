"""Backward-compatible re-export facade.

All functionality has been split into focused modules.
This module re-exports everything for existing callers that do
`from dopemux_pr_merge_specialist import engine` and then `engine.foo()`.
"""

from __future__ import annotations

from . import merge as _merge_module
from . import queue_drain as _queue_drain_module

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

_queue_scan_impl = _queue_drain_module.queue_scan
_pr_plan_impl = _queue_drain_module.pr_plan
_pr_apply_impl = _queue_drain_module.pr_apply
_pr_merge_impl = _queue_drain_module.pr_merge
_queue_drain_impl = _queue_drain_module.queue_drain
_update_remaining_pr_bases_impl = _queue_drain_module.update_remaining_pr_bases
_run_merge_with_fallback_impl = _merge_module.run_merge_with_fallback

_ENGINE_QUEUE_SCAN_WRAPPER = None
_ENGINE_PR_PLAN_WRAPPER = None
_ENGINE_PR_APPLY_WRAPPER = None
_ENGINE_PR_MERGE_WRAPPER = None
_ENGINE_QUEUE_DRAIN_WRAPPER = None
_ENGINE_RUN_MERGE_WITH_FALLBACK_WRAPPER = None


def _sync_queue_drain_bindings() -> None:
    """Keep engine monkeypatches visible to the queue_drain module."""
    engine_queue_scan = globals()["queue_scan"]
    engine_pr_plan = globals()["pr_plan"]
    engine_pr_apply = globals()["pr_apply"]
    engine_pr_merge = globals()["pr_merge"]
    engine_queue_drain = globals()["queue_drain"]
    engine_update_remaining_pr_bases = globals()["update_remaining_pr_bases"]

    _queue_drain_module.GitHubClient = GitHubClient
    _queue_drain_module.pr_apply = (
        _pr_apply_impl
        if engine_pr_apply is _ENGINE_PR_APPLY_WRAPPER
        else engine_pr_apply
    )
    _queue_drain_module.pr_merge = (
        _pr_merge_impl
        if engine_pr_merge is _ENGINE_PR_MERGE_WRAPPER
        else engine_pr_merge
    )
    _queue_drain_module.pr_plan = (
        _pr_plan_impl
        if engine_pr_plan is _ENGINE_PR_PLAN_WRAPPER
        else engine_pr_plan
    )
    _queue_drain_module.queue_scan = (
        _queue_scan_impl
        if engine_queue_scan is _ENGINE_QUEUE_SCAN_WRAPPER
        else engine_queue_scan
    )
    _queue_drain_module.queue_drain = (
        _queue_drain_impl
        if engine_queue_drain is _ENGINE_QUEUE_DRAIN_WRAPPER
        else engine_queue_drain
    )
    _queue_drain_module.update_remaining_pr_bases = (
        _update_remaining_pr_bases_impl
        if engine_update_remaining_pr_bases is _update_remaining_pr_bases_impl
        else engine_update_remaining_pr_bases
    )


def _sync_merge_bindings() -> None:
    _merge_module.execute_or_dry_run = globals()["execute_or_dry_run"]
    _merge_module.GitHubClient = GitHubClient


def queue_scan(*args, **kwargs):
    _sync_queue_drain_bindings()
    return _queue_drain_module.queue_scan(*args, **kwargs)


def pr_plan(*args, **kwargs):
    _sync_queue_drain_bindings()
    return _queue_drain_module.pr_plan(*args, **kwargs)


def pr_apply(*args, **kwargs):
    _sync_queue_drain_bindings()
    return _queue_drain_module.pr_apply(*args, **kwargs)


def pr_merge(*args, **kwargs):
    _sync_queue_drain_bindings()
    return _queue_drain_module.pr_merge(*args, **kwargs)


def queue_drain(*args, **kwargs):
    _sync_queue_drain_bindings()
    return _queue_drain_impl(*args, **kwargs)


def run_merge_with_fallback(*args, **kwargs):
    _sync_merge_bindings()
    return _run_merge_with_fallback_impl(*args, **kwargs)


_ENGINE_QUEUE_SCAN_WRAPPER = queue_scan
_ENGINE_PR_PLAN_WRAPPER = pr_plan
_ENGINE_PR_APPLY_WRAPPER = pr_apply
_ENGINE_PR_MERGE_WRAPPER = pr_merge
_ENGINE_QUEUE_DRAIN_WRAPPER = queue_drain
_ENGINE_RUN_MERGE_WITH_FALLBACK_WRAPPER = run_merge_with_fallback
