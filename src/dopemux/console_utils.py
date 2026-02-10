"""
Shared console utilities for Dopemux.

Provides a pre-configured Rich console with .logger adapter for consistent
logging across all modules.

This module re-exports the shared console from dopemux.console for backward compatibility.
"""

from .console import console


__all__ = ['console']
