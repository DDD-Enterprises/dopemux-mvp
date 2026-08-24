"""Deterministic evidence freshness and receipt-reuse eligibility.

No clock is read here: callers supply ``as_of`` explicitly so that identical
inputs always produce identical output. No network, no filesystem, no cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    Denial,
    EvidenceReference,
    FreshnessState,
    GovernedDeliveryEnvelope,
    Identity,
    NormalizedFailureClass,
    digest_of,
    parse_instant,
)

# The ten conjunctive conditions that define receipt-reuse eligibility.
# All must hold; any single false condition forces RECOMPUTE or STALE.
REUSE_CONDITIONS: tuple[str, ...] = (
    "same_subject_digest",
    "same_required_input_digests",
    "same_policy_digest",
    "same_schema_digest",
    "same_tool_or_validator_version",
    "same_environment_scope_when_environment_matters",
    "producer_identity_still_trusted",
    "not_expired_when_freshness_is_semantic",
    "not_superseded_or_tombstoned",
    "consumer_adds_no_distinct_authority_or_live_state_check",
)


@dataclass(frozen=True)
class FreshnessAssessment:
    """Why a reference holds the freshness state it does."""

    evidence_id: str
    state: FreshnessState
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "state": self.state.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReuseDecision:
    """Reuse eligibility with every condition's outcome enumerated.

    The per-condition map is what makes the decision auditable: a bare boolean
    could not distinguish a genuine pass from a vacuous one.
    """

    eligible: bool
    conditions: Mapping[str, bool]
    reason: str

    @property
    def failed_conditions(self) -> list[str]:
        return sorted(name for name, ok in self.conditions.items() if not ok)

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "conditions": {name: self.conditions[name] for name in sorted(self.conditions)},
            "failed_conditions": self.failed_conditions,
            "reason": self.reason,
        }


def assess_freshness(
    reference: EvidenceReference,
    *,
    as_of: str,
    superseded_ids: Iterable[str] = (),
) -> FreshnessAssessment:
    """Compute a reference's freshness against an explicit instant.

    Precedence is deliberate: tombstone, then supersession, then expiry, then
    the producer's own declared state. An unestablished state stays UNKNOWN
    rather than being optimistically read as CURRENT.
    """
    if reference.tombstone:
        return FreshnessAssessment(
            reference.evidence_id, FreshnessState.TOMBSTONED, "reference carries a tombstone"
        )

    if reference.evidence_id in set(superseded_ids):
        return FreshnessAssessment(
            reference.evidence_id,
            FreshnessState.SUPERSEDED,
            "a later reference supersedes this evidence_id",
        )

    now = parse_instant(as_of, field_name="as_of")

    if reference.valid_until is not None:
        expiry = parse_instant(reference.valid_until, field_name="valid_until")
        if now > expiry:
            return FreshnessAssessment(
                reference.evidence_id,
                FreshnessState.EXPIRED,
                f"valid_until {reference.valid_until} precedes as_of {as_of}",
            )

    if reference.freshness_state is FreshnessState.UNKNOWN:
        return FreshnessAssessment(
            reference.evidence_id,
            FreshnessState.UNKNOWN,
            "producer did not establish a freshness state; unknown fails closed",
        )

    if reference.freshness_state is not FreshnessState.CURRENT:
        return FreshnessAssessment(
            reference.evidence_id,
            reference.freshness_state,
            f"producer declared {reference.freshness_state.value}",
        )

    return FreshnessAssessment(
        reference.evidence_id, FreshnessState.CURRENT, "within validity and not superseded"
    )


def evaluate_receipt_reuse(
    *,
    candidate: EvidenceReference,
    required_subject_digest: str,
    as_of: str,
    required_input_digests: Sequence[str] = (),
    candidate_input_digests: Sequence[str] = (),
    required_policy_version: str | None = None,
    required_schema_version: str | None = None,
    required_tool_version: str | None = None,
    required_environment_digest: str | None = None,
    environment_matters: bool = False,
    trusted_producers: Iterable[str] = (),
    freshness_is_semantic: bool = True,
    consumer_adds_distinct_authority: bool = False,
    superseded_ids: Iterable[str] = (),
) -> ReuseDecision:
    """Decide whether a deterministic receipt may be reused.

    A receipt is reusable only when every input that defines its meaning is
    unchanged. A matching path or filename is never sufficient on its own.
    """
    subject = candidate.subject.content_digest or candidate.subject.head_sha
    freshness = assess_freshness(candidate, as_of=as_of, superseded_ids=superseded_ids)

    conditions: dict[str, bool] = {
        "same_subject_digest": bool(subject) and subject == required_subject_digest,
        "same_required_input_digests": list(candidate_input_digests) == list(required_input_digests),
        "same_policy_digest": required_policy_version is None
        or candidate.policy_version == required_policy_version,
        "same_schema_digest": required_schema_version is None
        or candidate.schema_version_used == required_schema_version,
        "same_tool_or_validator_version": required_tool_version is None
        or candidate.tool_version == required_tool_version,
        "same_environment_scope_when_environment_matters": (not environment_matters)
        or (
            required_environment_digest is not None
            and candidate.environment_digest == required_environment_digest
        ),
        "producer_identity_still_trusted": candidate.producer_identity in set(trusted_producers),
        "not_expired_when_freshness_is_semantic": (not freshness_is_semantic)
        or freshness.state is FreshnessState.CURRENT,
        "not_superseded_or_tombstoned": freshness.state
        not in {FreshnessState.SUPERSEDED, FreshnessState.TOMBSTONED},
        "consumer_adds_no_distinct_authority_or_live_state_check": (
            not consumer_adds_distinct_authority
        ),
    }

    if set(conditions) != set(REUSE_CONDITIONS):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            "receipt-reuse condition set does not match the declared predicate",
        )

    eligible = all(conditions.values())
    failed = sorted(name for name, ok in conditions.items() if not ok)
    reason = "all reuse conditions hold" if eligible else f"failed conditions: {', '.join(failed)}"
    return ReuseDecision(eligible=eligible, conditions=conditions, reason=reason)


def require_identity_match(
    reference: EvidenceReference, expected: Identity, *, context: str
) -> None:
    """Deny cross-project and cross-worktree reuse of a reference."""
    expected.require_compatible(reference.identity, context=context)


def check_idempotency_batch(
    envelopes: Sequence[GovernedDeliveryEnvelope],
) -> dict[str, str]:
    """Detect idempotency-key collisions within one caller-supplied batch.

    Same key with an identical payload is an accepted duplicate; same key with a
    different payload is denied. Nothing persists between calls: the supplied
    batch is the entire universe considered, since G0 keeps no cache.
    """
    seen: dict[str, str] = {}
    for envelope in envelopes:
        payload_digest = digest_of(envelope.as_dict()["payload"])
        existing = seen.get(envelope.idempotency_key)
        if existing is None:
            seen[envelope.idempotency_key] = payload_digest
        elif existing != payload_digest:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                f"idempotency_key {envelope.idempotency_key!r} reused with a different payload",
            )
    return seen
