"""UAG append-only physical-attempt lineage.

Physical attempts are lineage records appended under a logical request. The
lineage is append-only: existing records cannot be rewritten, removed, or
reordered in place. Every append produces a new lineage; the source lineage is
never mutated. A duplicate attempt id appends a new record (it is not treated
as an in-place rewrite), preserving replay/audit integrity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from dopemux.uag.enums import AttemptSemanticState
from dopemux.uag.primitives import DigestRef


@dataclass(frozen=True)
class AttemptRecord:
    """A single physical attempt (C0-R2 ``attempt_records`` item).

    ``provider_non_acceptance_evidence_ref`` must be present exactly when the
    semantic state is ``NON_ACCEPTANCE_PROVEN``.
    """

    attempt_id: str
    semantic_state: AttemptSemanticState
    selected_route_profile_id: str
    model_transport_receipt_ref: str | None = None
    provider_non_acceptance_evidence_ref: DigestRef | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.attempt_id, str) or not self.attempt_id:
            raise ValueError("attempt_id must be a non-empty string")
        if not isinstance(self.selected_route_profile_id, str) or not self.selected_route_profile_id:
            raise ValueError("selected_route_profile_id must be a non-empty string")
        if not isinstance(self.semantic_state, AttemptSemanticState):
            raise ValueError("semantic_state must be an AttemptSemanticState")
        is_non_acceptance = self.semantic_state is AttemptSemanticState.NON_ACCEPTANCE_PROVEN
        has_evidence = self.provider_non_acceptance_evidence_ref is not None
        if is_non_acceptance != has_evidence:
            raise ValueError(
                "NON_ACCEPTANCE_PROVEN requires provider_non_acceptance_evidence_ref, "
                "and that evidence ref is only valid for NON_ACCEPTANCE_PROVEN"
            )


@dataclass(frozen=True)
class AttemptLineage:
    """Append-only lineage of physical attempts.

    Immutable: ``append`` returns a new ``AttemptLineage`` and never mutates
    ``self``. Records are stored in arrival order and are never rewritten.
    """

    records: tuple[AttemptRecord, ...] = field(default_factory=tuple)

    def append(self, record: AttemptRecord) -> "AttemptLineage":
        if not isinstance(record, AttemptRecord):
            raise ValueError("append() expects an AttemptRecord")
        return AttemptLineage(records=self.records + (record,))

    def extend(self, records: Iterable[AttemptRecord]) -> "AttemptLineage":
        return AttemptLineage(records=self.records + tuple(records))

    def latest(self) -> AttemptRecord | None:
        return self.records[-1] if self.records else None

    def __len__(self) -> int:
        return len(self.records)
