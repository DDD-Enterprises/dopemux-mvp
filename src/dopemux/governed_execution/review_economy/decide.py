"""Pure reuse decision for a review request against prior receipts.

Pure module: no process spawning, no clock reads, no filesystem, no network.
"now" is always a caller-supplied RFC 3339 UTC string, never read from a
clock here. A ReviewDecision is advice to the caller: it never invokes a
reviewer and never carries execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from dopemux.governed_execution.review_economy.keys import (
    MODEL_REVIEWER_CLASSES,
    REVIEWER_CLASSES,
    ReceiptRef,
    ReviewReceiptKey,
    ReviewReceiptRecord,
    is_sha256,
    parse_rfc3339_utc,
)

TRIGGERS: frozenset[str] = frozenset(
    {
        "HEAD_MOVED",
        "POLICY_CHANGED",
        "RECEIPT_EXPIRED",
        "REVIEWER_INVALIDATED",
        "EXPLICIT_RERUN",
        "FREEZE_REACHED",
        "SETTLEMENT_REACHED",
    }
)
# The GitHub-draft-derived trigger is deliberately absent from TRIGGERS: no
# structured trigger here is sourced from a pull request's draft/ready flag.

DECISIONS: frozenset[str] = frozenset({"REUSE", "NEW_CALL", "BLOCKED"})

# Fixed priority order for NEW_CALL reason attribution: matches the order
# the invalidation conditions are listed in the packet invariant.
_REASON_PRIORITY: tuple[str, ...] = (
    "HEAD_MOVED",
    "POLICY_CHANGED",
    "RECEIPT_EXPIRED",
    "REVIEWER_INVALIDATED",
    "VERDICT_NOT_QUALIFYING",
    "SUBJECT_HEAD_MISMATCH",
    "NO_PRIOR_RECEIPT",
)


@dataclass(frozen=True)
class ReviewRequest:
    """A request to decide whether a review needs a fresh reviewer call.

    key may be None to exercise the fail-closed BLOCKED path for missing
    identity; trigger and explicit_rerun_authorized are validated eagerly
    because they are always caller-controlled scalars, never derived data
    that might legitimately arrive absent.
    """

    key: Optional[ReviewReceiptKey]
    trigger: str
    explicit_rerun_authorized: bool

    def __post_init__(self) -> None:
        if self.trigger not in TRIGGERS:
            raise ValueError(f"trigger not in closed set: {self.trigger!r}")
        if not isinstance(self.explicit_rerun_authorized, bool):
            raise ValueError(
                "explicit_rerun_authorized must be a bool: "
                f"{self.explicit_rerun_authorized!r}"
            )


@dataclass(frozen=True)
class ReviewPolicy:
    """The policy a decision is evaluated against.

    qualifying_verdicts may legally be empty: an empty qualifying set is a
    well-formed policy that can never yield REUSE, detected and reported by
    decide_review as BLOCKED rather than rejected at construction.
    """

    policy_digest: str
    qualifying_verdicts: frozenset[str]
    premium_classes: frozenset[str]

    def __post_init__(self) -> None:
        if not is_sha256(self.policy_digest):
            raise ValueError(
                f"policy_digest is not a sha256 digest: {self.policy_digest!r}"
            )
        if not isinstance(self.qualifying_verdicts, frozenset) or not all(
            isinstance(v, str) for v in self.qualifying_verdicts
        ):
            raise ValueError("qualifying_verdicts must be a frozenset of str")
        if not isinstance(self.premium_classes, frozenset) or not all(
            isinstance(v, str) for v in self.premium_classes
        ):
            raise ValueError("premium_classes must be a frozenset of str")
        unknown = self.premium_classes - REVIEWER_CLASSES
        if unknown:
            raise ValueError(f"premium_classes has unknown reviewer classes: {unknown!r}")


@dataclass(frozen=True)
class ReviewDecision:
    """The outcome of decide_review.

    authority and is_execution_authority are const: this decision is advice
    to the caller, never a reviewer invocation and never a grant of any kind.
    """

    decision: str
    reasons: tuple[str, ...]
    reused_receipt_ref: Optional[ReceiptRef]
    model_calls_avoided: int
    authority: str = field(default="NONE", init=False)
    is_execution_authority: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ValueError(f"decision not in closed set: {self.decision!r}")
        if not isinstance(self.reasons, tuple) or not all(
            isinstance(r, str) for r in self.reasons
        ):
            raise ValueError("reasons must be a tuple of str")
        if len(self.reasons) == 0:
            raise ValueError("reasons must not be empty")
        if not isinstance(self.model_calls_avoided, int) or isinstance(
            self.model_calls_avoided, bool
        ):
            raise ValueError(
                f"model_calls_avoided must be an int: {self.model_calls_avoided!r}"
            )
        if self.model_calls_avoided < 0:
            raise ValueError("model_calls_avoided must not be negative")


def _blocked(reason: str) -> ReviewDecision:
    return ReviewDecision(
        decision="BLOCKED",
        reasons=(reason,),
        reused_receipt_ref=None,
        model_calls_avoided=0,
    )


def _new_call(reasons: tuple[str, ...]) -> ReviewDecision:
    return ReviewDecision(
        decision="NEW_CALL",
        reasons=reasons,
        reused_receipt_ref=None,
        model_calls_avoided=0,
    )


def _reuse(record: ReviewReceiptRecord, reviewer_class: str) -> ReviewDecision:
    avoided = 1 if reviewer_class in MODEL_REVIEWER_CLASSES else 0
    return ReviewDecision(
        decision="REUSE",
        reasons=("QUALIFYING_RECEIPT_FOUND",),
        reused_receipt_ref=record.receipt_ref,
        model_calls_avoided=avoided,
    )


def decide_review(
    request: ReviewRequest,
    existing: Sequence[ReviewReceiptRecord],
    now: str,
    policy: ReviewPolicy,
) -> ReviewDecision:
    """Decide REUSE, NEW_CALL or BLOCKED for one review request.

    Fails closed to BLOCKED on any missing or malformed input; never returns
    REUSE in that case. Otherwise: explicit_rerun_authorized always forces
    NEW_CALL; a qualifying, unexpired, non-invalidated receipt with an equal
    key and matching subject head forces REUSE; anything else is NEW_CALL
    with the specific reasons that ruled out reuse, in a fixed stable order.
    """
    if not isinstance(request, ReviewRequest):
        return _blocked("MALFORMED_REQUEST")
    if not isinstance(request.key, ReviewReceiptKey):
        return _blocked("MISSING_KEY")
    if not isinstance(policy, ReviewPolicy):
        return _blocked("MALFORMED_POLICY")
    if len(policy.qualifying_verdicts) == 0:
        return _blocked("EMPTY_QUALIFYING_VERDICTS")
    if not isinstance(now, str):
        return _blocked("MALFORMED_NOW")
    try:
        now_dt = parse_rfc3339_utc(now)
    except ValueError:
        return _blocked("MALFORMED_NOW")

    validated_existing: list[ReviewReceiptRecord] = []
    for record in existing:
        if not isinstance(record, ReviewReceiptRecord):
            return _blocked("MALFORMED_RECORD")
        validated_existing.append(record)

    if request.explicit_rerun_authorized:
        return _new_call(("EXPLICIT_RERUN",))

    request_key = request.key

    for record in validated_existing:
        if record.key.digest != request_key.digest:
            continue
        if record.verdict not in policy.qualifying_verdicts:
            continue
        if record.invalidated:
            continue
        if parse_rfc3339_utc(record.expires_at) <= now_dt:
            continue
        if record.subject_head != request_key.head_sha:
            continue
        return _reuse(record, request_key.reviewer_class)

    same_subject = [
        record
        for record in validated_existing
        if record.key.review_type == request_key.review_type
        and record.key.reviewer_class == request_key.reviewer_class
    ]

    applicable: set[str] = set()
    for record in same_subject:
        if record.key.head_sha != request_key.head_sha:
            applicable.add("HEAD_MOVED")
            continue
        if record.key.policy_digest != request_key.policy_digest:
            applicable.add("POLICY_CHANGED")
            continue
        if parse_rfc3339_utc(record.expires_at) <= now_dt:
            applicable.add("RECEIPT_EXPIRED")
        if record.invalidated:
            applicable.add("REVIEWER_INVALIDATED")
        if record.verdict not in policy.qualifying_verdicts:
            applicable.add("VERDICT_NOT_QUALIFYING")
        if record.subject_head != request_key.head_sha:
            applicable.add("SUBJECT_HEAD_MISMATCH")

    if not applicable:
        applicable.add("NO_PRIOR_RECEIPT")

    reasons = tuple(reason for reason in _REASON_PRIORITY if reason in applicable)
    return _new_call(reasons)
