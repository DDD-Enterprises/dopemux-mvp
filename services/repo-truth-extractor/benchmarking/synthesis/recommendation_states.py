from __future__ import annotations

from dataclasses import dataclass

from ..policies.loader import load_policy_pack
from .freshness import FreshnessOutcome


_POLICY = load_policy_pack("recommendation_state_policy_v1.json")


@dataclass(frozen=True)
class RecommendationOutcome:
    recommendation_state: str
    failed_gates: list[str]
    freshness_state: str
    dispute_state: str
    requires_review: bool
    required_action: str


def determine_recommendation_state(
    attempt: dict[str, object],
    freshness: FreshnessOutcome,
    blockers: list[str],
) -> RecommendationOutcome:
    blocker_set = set(blockers)
    if blocker_set.intersection(set(_POLICY["quarantine_blockers"])):
        return RecommendationOutcome(
            recommendation_state="quarantined",
            failed_gates=sorted(blocker_set),
            freshness_state=freshness.freshness_state,
            dispute_state=freshness.dispute_state,
            requires_review=True,
            required_action="quarantine_and_investigate",
        )
    if freshness.freshness_state == "stale" or freshness.dispute_state != "clear":
        return RecommendationOutcome(
            recommendation_state="stale_disputed",
            failed_gates=sorted(blocker_set),
            freshness_state=freshness.freshness_state,
            dispute_state=freshness.dispute_state,
            requires_review=True,
            required_action="refresh_evidence_or_clear_dispute",
        )
    if blocker_set.intersection(set(_POLICY["experimental_only_blockers"])):
        return RecommendationOutcome(
            recommendation_state="experimental_only",
            failed_gates=sorted(blocker_set),
            freshness_state=freshness.freshness_state,
            dispute_state=freshness.dispute_state,
            requires_review=True,
            required_action="limit_to_experimental_lab",
        )
    severe_ineligibility = set(_POLICY["ineligible_blockers"])
    if blocker_set.intersection(severe_ineligibility):
        return RecommendationOutcome(
            recommendation_state="ineligible",
            failed_gates=sorted(blocker_set),
            freshness_state=freshness.freshness_state,
            dispute_state=freshness.dispute_state,
            requires_review=False,
            required_action="hold_from_promotion",
        )
    review_only = set(_POLICY["review_only_blockers"])
    if blocker_set.intersection(review_only):
        return RecommendationOutcome(
            recommendation_state="eligible_for_review",
            failed_gates=sorted(blocker_set),
            freshness_state=freshness.freshness_state,
            dispute_state=freshness.dispute_state,
            requires_review=True,
            required_action="manual_governance_review",
        )
    return RecommendationOutcome(
        recommendation_state="recommended_for_review",
        failed_gates=[],
        freshness_state=freshness.freshness_state,
        dispute_state=freshness.dispute_state,
        requires_review=True,
        required_action="manual_promotion_review",
    )
