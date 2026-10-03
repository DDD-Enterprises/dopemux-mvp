"""PR Steward boundary: a fail-closed classifier over proposed steward actions.

The PR Steward may check and report; it may never fix, approve, merge or
author an audit. This module exposes no function that performs any of
those forbidden operations -- it only classifies action names drawn from a
closed vocabulary. Unknown action names are FORBIDDEN (fail closed).
"""

from __future__ import annotations

CHECK_ONLY = "CHECK_ONLY"
NO_FIX = "NO_FIX"
NO_APPROVAL = "NO_APPROVAL"
NO_MERGE = "NO_MERGE"
NO_AUDIT_AUTHORING = "NO_AUDIT_AUTHORING"

ALLOWED = "ALLOWED"
FORBIDDEN = "FORBIDDEN"

# READY is a classification string only -- this module computes no readiness
# value and exposes no function that would grant it.
READY = "READY"
NOT_READY = "NOT_READY"

ALLOWED_ACTIONS = frozenset(
    {
        "READ_PR",
        "READ_CHECKS",
        "READ_REVIEWS",
        "COMPUTE_READINESS",
        "EMIT_READINESS_CLASSIFICATION",
    }
)

FORBIDDEN_ACTIONS = frozenset(
    {
        "PUSH_FIX",
        "COMMIT",
        "APPROVE_REVIEW",
        "REQUEST_CHANGES",
        "MERGE",
        "MARK_READY",
        "AUTHOR_AUDIT",
        "WRITE_PROOF",
        "MODIFY_BRANCH_PROTECTION",
    }
)


def classify_steward_action(action: str) -> str:
    """Return ``ALLOWED`` or ``FORBIDDEN``. Unknown actions are FORBIDDEN."""
    if action in ALLOWED_ACTIONS:
        return ALLOWED
    return FORBIDDEN
