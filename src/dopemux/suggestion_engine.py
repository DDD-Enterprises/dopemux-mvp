"""Compatibility suggestion engine helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SuggestionEvaluation:
    """Decision envelope for profile suggestion prompting."""

    should_prompt: bool
    reason: str
    match: object | None = None


def evaluate_suggestion(detector, service, current_profile=None) -> SuggestionEvaluation:
    """Evaluate whether a profile switch suggestion should be shown."""

    config = service.config
    if not getattr(config, "enabled", True):
        return SuggestionEvaluation(False, "service_disabled")

    if callable(getattr(config, "is_quiet_hours", None)) and config.is_quiet_hours():
        return SuggestionEvaluation(False, "quiet_hours")

    match = detector.detect(context=None)
    if match is None:
        return SuggestionEvaluation(False, "no_match")

    active = current_profile if current_profile is not None else getattr(service, "current_profile", None)
    if active == match.profile_name:
        return SuggestionEvaluation(False, "already_active", match=match)

    threshold = float(getattr(config, "confidence_threshold", 0.85))
    if float(match.confidence) < threshold:
        return SuggestionEvaluation(False, "below_threshold", match=match)

    never_suggest = getattr(config, "never_suggest", set()) or set()
    if match.profile_name in never_suggest:
        return SuggestionEvaluation(False, "never_suggest", match=match)

    if not service.should_suggest(match.profile_name, match.confidence):
        return SuggestionEvaluation(False, "service_policy_blocked", match=match)

    return SuggestionEvaluation(True, "service_policy_allows", match=match)


def suggest_if_needed(service, detector, current_profile=None):
    """Perform suggestion side effect and return accepted profile name if any."""

    evaluation = evaluate_suggestion(detector=detector, service=service, current_profile=current_profile)
    if not evaluation.should_prompt or evaluation.match is None:
        return None

    match = evaluation.match
    if service.suggest_profile_switch(match.profile_name, match):
        service.current_profile = match.profile_name
        return match.profile_name
    return None

