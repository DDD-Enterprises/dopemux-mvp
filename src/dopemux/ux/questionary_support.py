"""Shared questionary loading for interactive Dopemux UX surfaces."""

from __future__ import annotations

import importlib


QUESTIONARY_INSTALL_MESSAGE = (
    "Interactive Dopemux UX requires `questionary`. "
    "Run `uv sync --frozen --extra test --extra services` or install `questionary` "
    "before using wizard or interactive prompt surfaces."
)


class MissingInteractiveDependencyError(RuntimeError):
    """Raised when required interactive UX dependencies are unavailable."""


def require_questionary():
    """Import questionary lazily with a deterministic install hint."""
    try:
        return importlib.import_module("questionary")
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise MissingInteractiveDependencyError(QUESTIONARY_INSTALL_MESSAGE) from exc


__all__ = [
    "MissingInteractiveDependencyError",
    "QUESTIONARY_INSTALL_MESSAGE",
    "require_questionary",
]
