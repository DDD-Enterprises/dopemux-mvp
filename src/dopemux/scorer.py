"""
Profile scoring facade.

Referenced by historical Epic-2 deliverables as a standalone scorer module.
"""

from typing import Dict, Optional

from .profile_detector import DetectionContext, ProfileDetector, ProfileMatch


def score_all_profiles(
    context: Optional[DetectionContext] = None,
    detector: Optional[ProfileDetector] = None,
) -> Dict[str, ProfileMatch]:
    """Return score breakdown for all known profiles."""
    runtime_detector = detector or ProfileDetector()
    return runtime_detector.get_all_scores(context=context)


def score_best_profile(
    context: Optional[DetectionContext] = None,
    detector: Optional[ProfileDetector] = None,
) -> ProfileMatch:
    """Return best profile match for the given context."""
    runtime_detector = detector or ProfileDetector()
    return runtime_detector.detect(context=context)

