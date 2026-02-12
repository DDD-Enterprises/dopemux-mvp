"""Compatibility signal collection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DetectionSnapshot:
    """Bundle of gathered detection context and resulting scores."""

    context: object
    match: object
    signal_scores: dict[str, float]


def collect_detection_signals(detector, workspace: Path | None = None) -> DetectionSnapshot:
    """Gather detector context, apply workspace override, and score signals."""

    context = detector._gather_context()
    if workspace is not None:
        context.current_dir = Path(workspace).resolve()
    match = detector.detect(context=context)
    signal_scores = dict(getattr(match, "signal_scores", {}) or {})
    return DetectionSnapshot(context=context, match=match, signal_scores=signal_scores)

