"""Pure lifecycle projection: implement -> ... -> finality.

Pure module: no process spawning, no clock reads, no filesystem, no network.
This module only projects legal stage transitions; it never enforces them
against a real packet and never invokes an auditor.
"""
from __future__ import annotations

from enum import Enum
from typing import Tuple


class LifecycleStage(str, Enum):
    """The fixed-order lifecycle stages a packet projects through."""

    IMPLEMENT = "IMPLEMENT"
    VALIDATE = "VALIDATE"
    PR = "PR"
    CI_REVIEWS = "CI_REVIEWS"
    REPAIR = "REPAIR"
    REVIEW_SETTLED = "REVIEW_SETTLED"
    FREEZE = "FREEZE"
    FINAL_AUDIT = "FINAL_AUDIT"
    FINALITY = "FINALITY"


EVENTS: frozenset[str] = frozenset(
    {
        "VALIDATION_STARTED",
        "PR_OPENED",
        "CI_REVIEWS_STARTED",
        "REPAIR_NEEDED",
        "SETTLEMENT_REACHED",
        "REPAIR_COMPLETE",
        "FREEZE_REACHED",
        "FINAL_AUDIT_STARTED",
        "FINAL_AUDIT_PASSED",
        "FINAL_AUDIT_FAILED",
    }
)


class IllegalStage(Exception):
    """Raised for any (stage, event) pair that is not a legal transition."""


class FinalAuditAlreadyConsumed(Exception):
    """Raised when FINAL_AUDIT is entered a second time for one freeze_ref."""


_TRANSITIONS: dict[Tuple[LifecycleStage, str], LifecycleStage] = {
    (LifecycleStage.IMPLEMENT, "VALIDATION_STARTED"): LifecycleStage.VALIDATE,
    (LifecycleStage.VALIDATE, "PR_OPENED"): LifecycleStage.PR,
    (LifecycleStage.PR, "CI_REVIEWS_STARTED"): LifecycleStage.CI_REVIEWS,
    (LifecycleStage.CI_REVIEWS, "REPAIR_NEEDED"): LifecycleStage.REPAIR,
    (LifecycleStage.CI_REVIEWS, "SETTLEMENT_REACHED"): LifecycleStage.REVIEW_SETTLED,
    (LifecycleStage.REPAIR, "REPAIR_COMPLETE"): LifecycleStage.VALIDATE,
    (LifecycleStage.REVIEW_SETTLED, "FREEZE_REACHED"): LifecycleStage.FREEZE,
    (LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED"): LifecycleStage.FINAL_AUDIT,
    (LifecycleStage.FINAL_AUDIT, "FINAL_AUDIT_PASSED"): LifecycleStage.FINALITY,
    (LifecycleStage.FINAL_AUDIT, "FINAL_AUDIT_FAILED"): LifecycleStage.REPAIR,
}


def _coerce_stage(stage: object) -> LifecycleStage:
    if isinstance(stage, LifecycleStage):
        return stage
    if isinstance(stage, str):
        try:
            return LifecycleStage(stage)
        except ValueError as exc:
            raise IllegalStage(f"unknown stage: {stage!r}") from exc
    raise IllegalStage(f"stage must be a LifecycleStage or str: {stage!r}")


def advance(
    stage: object,
    event: object,
    freeze_ref: object,
    seen_final_audits: frozenset[str],
) -> Tuple[LifecycleStage, frozenset[str]]:
    """Project the next lifecycle stage for one (stage, event) transition.

    Returns (new_stage, new_seen_final_audits). Raises IllegalStage for any
    pair that is not one of the ten legal edges. Raises
    FinalAuditAlreadyConsumed when the transition would enter FINAL_AUDIT for
    a freeze_ref already present in seen_final_audits: a fresh FreezeReceipt
    (a new freeze_ref) is required to enter FINAL_AUDIT again.
    """
    current = _coerce_stage(stage)
    if not isinstance(event, str) or event not in EVENTS:
        raise IllegalStage(f"unknown event: {event!r}")
    if not isinstance(seen_final_audits, frozenset) or not all(
        isinstance(item, str) for item in seen_final_audits
    ):
        raise IllegalStage("seen_final_audits must be a frozenset of str")

    key = (current, event)
    if key not in _TRANSITIONS:
        raise IllegalStage(f"no legal transition from {current.value} on {event}")

    new_stage = _TRANSITIONS[key]

    if new_stage is LifecycleStage.FINAL_AUDIT:
        if not isinstance(freeze_ref, str) or len(freeze_ref) == 0:
            raise IllegalStage(f"freeze_ref must be a non-empty string: {freeze_ref!r}")
        if freeze_ref in seen_final_audits:
            raise FinalAuditAlreadyConsumed(freeze_ref)
        return new_stage, frozenset(seen_final_audits | {freeze_ref})

    return new_stage, seen_final_audits
