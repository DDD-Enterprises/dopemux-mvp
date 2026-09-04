"""UAG semantic core composition.

A frozen container tying together the immutable logical request, the append-only
attempt lineage, the identity chain, the mapping ledger, and deterministic
receipts. It exposes NO execution, approval, retry, fallback, or tool surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from dopemux.uag.attempt import AttemptLineage
from dopemux.uag.identity import IdentityChain
from dopemux.uag.ledger import MappingLedger
from dopemux.uag.receipt import Receipt
from dopemux.uag.request import LogicalRequest


@dataclass(frozen=True)
class SemanticCore:
    """Frozen snapshot of a logical request's semantic-core state.

    All sub-structures are immutable and append-only. Nothing here executes,
    approves, retries, or falls back. Reconstruct via the `*_with_*` helpers,
    which return new snapshots and never mutate the receiver.
    """

    request: LogicalRequest
    identity_chain: IdentityChain
    attempt_lineage: AttemptLineage
    ledger: MappingLedger
    receipts: tuple[Receipt, ...]

    def with_identity(self, chain: IdentityChain) -> "SemanticCore":
        return SemanticCore(
            request=self.request,
            identity_chain=chain,
            attempt_lineage=self.attempt_lineage,
            ledger=self.ledger,
            receipts=self.receipts,
        )

    def with_attempts(self, lineage: AttemptLineage) -> "SemanticCore":
        return SemanticCore(
            request=self.request,
            identity_chain=self.identity_chain,
            attempt_lineage=lineage,
            ledger=self.ledger,
            receipts=self.receipts,
        )

    def with_receipt(self, receipt: Receipt) -> "SemanticCore":
        return SemanticCore(
            request=self.request,
            identity_chain=self.identity_chain,
            attempt_lineage=self.attempt_lineage,
            ledger=self.ledger,
            receipts=self.receipts + (receipt,),
        )
