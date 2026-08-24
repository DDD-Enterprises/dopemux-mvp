"""Singleton registry for active spend tracker state.

This module maintains a stable identity across reloads to ensure that dual
importlib loads of v5 do not desync tracker state. The registry itself is
pinned to this module and persists in sys.modules, providing a single
canonical source of truth for tracker state.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from extractor.costing import SpendTrackerState


class SpendTrackerRegistry:
    """Thread-safe singleton registry for the active spend tracker."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_tracker: SpendTrackerState | None = None

    def get(self) -> SpendTrackerState | None:
        """Get the current active spend tracker state.

        Note: This acquires a lock; use with_lock for operations requiring
        sustained lock ownership.
        """
        with self._lock:
            return self._active_tracker

    def set(self, tracker: SpendTrackerState | None) -> None:
        """Set the active spend tracker state."""
        with self._lock:
            self._active_tracker = tracker

    @contextmanager
    def with_lock(self) -> Iterator[SpendTrackerState | None]:
        """Context manager yielding the current tracker state with lock held.

        Yields:
            SpendTrackerState | None: The active tracker state.

        Example:
            with registry.with_lock() as state:
                if state is not None:
                    state.total_cost_usd += cost
        """
        with self._lock:
            yield self._active_tracker


# Module-level singleton registry
_REGISTRY = SpendTrackerRegistry()


def get_registry() -> SpendTrackerRegistry:
    """Get the module-level spend tracker registry.

    Returns:
        SpendTrackerRegistry: The singleton registry pinned to this module.
        This identity is stable across reloads.
    """
    return _REGISTRY
