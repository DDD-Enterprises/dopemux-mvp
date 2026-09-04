"""UAG mapping / correlation ledger primitives.

The mapping ledger records correlations between logical requests, physical
attempts, identity stages, and receipts. It is data only: it grants no
ToolContract authority, performs no tool execution, and performs no retry or
fallback. Entries are append-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from dopemux.uag.enums import EvidenceStatus


class CorrelationKind(str, Enum):
    REQUEST_TO_ATTEMPT = "REQUEST_TO_ATTEMPT"
    ATTEMPT_TO_IDENTITY_STAGE = "ATTEMPT_TO_IDENTITY_STAGE"
    ATTEMPT_TO_RECEIPT = "ATTEMPT_TO_RECEIPT"
    IDENTITY_STAGE_TO_EVIDENCE = "IDENTITY_STAGE_TO_EVIDENCE"
    REQUEST_TO_IDENTITY_CHAIN = "REQUEST_TO_IDENTITY_CHAIN"


@dataclass(frozen=True)
class LedgerEntry:
    """A single correlation record in the mapping ledger."""

    entry_id: str
    kind: CorrelationKind
    left_ref: str
    right_ref: str
    evidence_status: EvidenceStatus = EvidenceStatus.OBSERVED
    notes: str | None = None

    def __post_init__(self) -> None:
        for name in ("entry_id", "left_ref", "right_ref"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"LedgerEntry.{name} must be non-empty")
        if not isinstance(self.kind, CorrelationKind):
            raise ValueError("kind must be a CorrelationKind")
        if not isinstance(self.evidence_status, EvidenceStatus):
            raise ValueError("evidence_status must be an EvidenceStatus")


@dataclass(frozen=True)
class MappingLedger:
    """Append-only correlation ledger.

    ``add`` returns a new ledger and never mutates the receiver. The ledger has
    no execution or approval surface.
    """

    entries: tuple[LedgerEntry, ...] = field(default_factory=tuple)

    def add(self, entry: LedgerEntry) -> "MappingLedger":
        if not isinstance(entry, LedgerEntry):
            raise ValueError("add() expects a LedgerEntry")
        return MappingLedger(entries=self.entries + (entry,))

    def for_kind(self, kind: CorrelationKind) -> tuple[LedgerEntry, ...]:
        if not isinstance(kind, CorrelationKind):
            raise ValueError("kind must be a CorrelationKind; raw strings are rejected")
        return tuple(e for e in self.entries if e.kind is kind)

    def __len__(self) -> int:
        return len(self.entries)
