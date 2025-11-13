"""
Legacy workspace utility wrappers.

Historically the Dopemux CLI imported helpers from this module. To ensure
backwards compatibility while centralising detection logic, these wrappers now
delegate to :mod:`dopemux.workspace_detection`.
"""

from pathlib import Path
from typing import Optional

from .workspace_detection import get_workspace_root as _detect_workspace_root


def get_workspace_root(start_path: Optional[Path] = None) -> Path:
    """
    Backwards-compatible shim that forwards to the unified workspace detector.

    Args:
        start_path: Optional starting directory for detection.

    Returns:
        Absolute workspace path resolved by dopemux.workspace_detection.
    """
    return _detect_workspace_root(start_path)
