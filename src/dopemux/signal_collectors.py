"""
Profile detection signal collection helpers.

This module provides an explicit ``signal_collectors`` entrypoint referenced by
historical implementation plans while delegating to ProfileDetector runtime logic.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .profile_detector import DetectionContext, ProfileDetector


@dataclass
class SignalSnapshot:
    """Collected profile-detection signals for a workspace."""

    context: DetectionContext
    signal_scores: Dict[str, float]


def collect_detection_signals(
    detector: Optional[ProfileDetector] = None,
    workspace: Optional[Path] = None,
) -> SignalSnapshot:
    """
    Collect current profile detection signals.

    Args:
        detector: Optional detector instance to reuse.
        workspace: Optional workspace path override.

    Returns:
        SignalSnapshot containing context and best-match score breakdown.
    """
    runtime_detector = detector or ProfileDetector()
    context = runtime_detector._gather_context()  # noqa: SLF001 - intentional reuse
    if workspace is not None:
        context.current_dir = workspace.resolve()
    match = runtime_detector.detect(context)
    return SignalSnapshot(context=context, signal_scores=match.signal_scores)

