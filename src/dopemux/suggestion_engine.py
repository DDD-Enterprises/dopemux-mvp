"""
Suggestion engine facade for profile auto-detection UX flows.

This compatibility module exposes a stable ``dopemux.suggestion_engine`` path
while delegating behavior to ``ProfileDetector`` and ``AutoDetectionService``.
"""

from dataclasses import dataclass
from typing import Optional

from .auto_detection_service import AutoDetectionService
from .profile_detector import (
    DetectionContext,
    ProfileDetector,
    ProfileMatch,
    format_match_summary,
)


@dataclass
class SuggestionEvaluation:
    """Decision payload for profile-switch suggestion evaluation."""

    match: ProfileMatch
    should_prompt: bool
    reason: str


def evaluate_suggestion(
    detector: Optional[ProfileDetector] = None,
    service: Optional[AutoDetectionService] = None,
    context: Optional[DetectionContext] = None,
    current_profile: Optional[str] = None,
) -> SuggestionEvaluation:
    """
    Evaluate whether profile switch should be suggested for current context.

    Without a service instance, evaluation falls back to detector confidence.
    With a service instance, full policy gates are applied (quiet hours,
    debounce, never-list, current profile, confidence threshold, enable flag).
    """
    runtime_detector = detector or ProfileDetector()
    match = runtime_detector.detect(context=context)

    if service is None:
        should_prompt = match.should_suggest()
        reason = "confidence_threshold_met" if should_prompt else "confidence_below_threshold"
        return SuggestionEvaluation(match=match, should_prompt=should_prompt, reason=reason)

    if current_profile is not None:
        service.current_profile = current_profile

    should_prompt = service.should_suggest(match.profile_name, match.confidence)
    if should_prompt:
        reason = "service_policy_allows"
    elif not service.config.enabled:
        reason = "service_disabled"
    elif match.confidence < service.config.confidence_threshold:
        reason = "confidence_below_service_threshold"
    elif service.config.is_quiet_hours():
        reason = "quiet_hours"
    elif match.profile_name in service.config.never_suggest:
        reason = "never_suggest"
    elif match.profile_name == service.current_profile:
        reason = "already_active"
    else:
        reason = "debounced_or_policy_blocked"

    return SuggestionEvaluation(match=match, should_prompt=should_prompt, reason=reason)


def suggest_if_needed(
    service: AutoDetectionService,
    detector: Optional[ProfileDetector] = None,
    context: Optional[DetectionContext] = None,
    current_profile: Optional[str] = None,
) -> Optional[str]:
    """
    Prompt and return suggested profile name if accepted; otherwise ``None``.
    """
    evaluation = evaluate_suggestion(
        detector=detector,
        service=service,
        context=context,
        current_profile=current_profile,
    )
    if not evaluation.should_prompt:
        return None

    if service.suggest_profile_switch(evaluation.match.profile_name, evaluation.match):
        service.current_profile = evaluation.match.profile_name
        return evaluation.match.profile_name
    return None


def render_suggestion_summary(match: ProfileMatch) -> str:
    """Return formatted ADHD-friendly match summary for UI/CLI surfaces."""
    return format_match_summary(match)

