"""Read-only reconciliation between desired (catalog-v2) and observed
(lease + ownership) service state (P1 fleet control plane).

Emits recommendations and data only -- there is no start/stop/rm/adopt/
migrate executor here or anywhere else in P1. See
``docs/03-reference/mcp/multiproject-falsification-contract.md`` hard
property 6 ("No foreign or ambiguous process/container/volume/lease is
mutated automatically") and P1_CONTRACT.md's reconcile section.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from dopemux.mcp.ownership import OwnershipEvidence


class ReconcileStatus(StrEnum):
    MATCHED = "MATCHED"
    MISSING = "MISSING"
    FOREIGN = "FOREIGN"
    AMBIGUOUS = "AMBIGUOUS"
    STALE = "STALE"
    LEGACY_UNBOUND = "LEGACY_UNBOUND"


_FOREIGN_LEASE_VERDICTS = frozenset({"WRONG_PROJECT", "WRONG_INSTANCE", "CONFLICTING"})
_ABSENT_LEASE_VERDICTS = frozenset({"UNKNOWN", "RELEASED"})


@dataclass(frozen=True)
class ServiceReconcileEntry:
    service_id: str
    status: ReconcileStatus
    recommendation: str
    lease_verdict: str
    ownership: Optional[OwnershipEvidence] = None


@dataclass(frozen=True)
class ReconcileReport:
    project_id: Optional[str]
    workspace_id: Optional[str]
    instance_id: Optional[str]
    entries: Tuple[ServiceReconcileEntry, ...]

    def by_status(self, status: ReconcileStatus) -> Tuple[ServiceReconcileEntry, ...]:
        return tuple(e for e in self.entries if e.status == status)


def reconcile_service(
    *,
    service_id: str,
    lease_verdict: str,
    ownership: Optional[OwnershipEvidence] = None,
    has_legacy_unmigrated_record: bool = False,
) -> ServiceReconcileEntry:
    """Classify one service's desired-vs-observed state. Pure function --
    every input is caller-supplied evidence (a ``service_leases.lease_verdict``
    result and an optional ``ownership.OwnershipEvidence``); this never
    queries Docker, the registry, or leases itself."""

    if lease_verdict in _FOREIGN_LEASE_VERDICTS:
        return ServiceReconcileEntry(
            service_id=service_id,
            status=ReconcileStatus.FOREIGN,
            recommendation="do not adopt; endpoint is bound to a different project/instance/owner",
            lease_verdict=lease_verdict,
            ownership=ownership,
        )

    if lease_verdict == "STALE":
        return ServiceReconcileEntry(
            service_id=service_id,
            status=ReconcileStatus.STALE,
            recommendation="re-verify ownership evidence before reusing this lease",
            lease_verdict=lease_verdict,
            ownership=ownership,
        )

    if lease_verdict in _ABSENT_LEASE_VERDICTS:
        if has_legacy_unmigrated_record:
            return ServiceReconcileEntry(
                service_id=service_id,
                status=ReconcileStatus.LEGACY_UNBOUND,
                recommendation="a legacy v1 lease exists for this service; explicit operator "
                "migration required (see service_leases.preview_legacy_migration)",
                lease_verdict=lease_verdict,
                ownership=ownership,
            )
        return ServiceReconcileEntry(
            service_id=service_id,
            status=ReconcileStatus.MISSING,
            recommendation="acquire a lease if this service is desired for this identity",
            lease_verdict=lease_verdict,
            ownership=ownership,
        )

    if lease_verdict == "ACTIVE" and ownership is not None and ownership.classification == "OWNED":
        return ServiceReconcileEntry(
            service_id=service_id,
            status=ReconcileStatus.MATCHED,
            recommendation="no action needed",
            lease_verdict=lease_verdict,
            ownership=ownership,
        )

    return ServiceReconcileEntry(
        service_id=service_id,
        status=ReconcileStatus.AMBIGUOUS,
        recommendation="gather additional ownership evidence (registry/lease/probe/storage) "
        "before any mutation is considered",
        lease_verdict=lease_verdict,
        ownership=ownership,
    )
