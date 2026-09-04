"""UAG deterministic receipts.

A receipt is a deterministic, hash-bound record of what happened. Receipts are
produced from canonical serialization so the same inputs always yield the same
digest. Receipts carry no execution authority and make no exactly-once claim
(exactly-once is FORBIDDEN in C0-R2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dopemux.uag.enums import AttemptSemanticState, ExecutionAuthority
from dopemux.uag.primitives import canonical_digest, is_sha256


@dataclass(frozen=True)
class Receipt:
    """A deterministic receipt bound to a digest.

    ``execution_authority`` is always ``NONE``; ``exactly_once_claim`` is
    enforced to the literal ``"FORBIDDEN"`` string and can never be a claim.
    """

    receipt_id: str
    digest: str
    subject_ref: str
    semantic_state: AttemptSemanticState
    execution_authority: ExecutionAuthority = ExecutionAuthority.NONE
    exactly_once_claim: str = "FORBIDDEN"

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str) or not self.receipt_id:
            raise ValueError("receipt_id must be a non-empty string")
        if not isinstance(self.subject_ref, str) or not self.subject_ref:
            raise ValueError("subject_ref must be a non-empty string")
        if not is_sha256(self.digest):
            raise ValueError("digest must be a lowercase 64-char hex digest")
        if not isinstance(self.semantic_state, AttemptSemanticState):
            raise ValueError("semantic_state must be an AttemptSemanticState")
        if self.exactly_once_claim != "FORBIDDEN":
            raise ValueError("exactly_once_claim must be the literal FORBIDDEN")


def deterministic_receipt(
    receipt_id: str,
    subject_ref: str,
    semantic_state: AttemptSemanticState,
    payload: Any,
) -> Receipt:
    """Build a receipt whose digest is the canonical digest of ``payload``.

    Deterministic: identical inputs yield an identical digest. ``payload`` is
    never interpreted; it is serialized canonically for binding only.
    """
    digest = canonical_digest(payload)
    return Receipt(
        receipt_id=receipt_id,
        digest=digest,
        subject_ref=subject_ref,
        semantic_state=semantic_state,
    )
