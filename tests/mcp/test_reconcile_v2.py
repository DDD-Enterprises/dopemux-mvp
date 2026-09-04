"""P1 read-only reconciliation: all six statuses, zero mutation surface.

Covers Task 7 (reconcile half) of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-
PLANE-001.
"""

from __future__ import annotations

from dopemux.mcp.ownership import (
    LeaseEvidence,
    OwnershipEvidence,
    ProbeEvidence,
    RegistryEvidence,
    StorageEvidence,
    evaluate_ownership,
)
from dopemux.mcp.reconcile import ReconcileStatus, reconcile_service


def _owned_evidence() -> OwnershipEvidence:
    return evaluate_ownership(
        registry=RegistryEvidence(verified=True, project_id="p", registry_generation=1),
        lease=LeaseEvidence(verified=True, lease_id="l"),
        probe=ProbeEvidence(verified=True, service_family="conport"),
        storage=StorageEvidence(verified=True, evidence="mount"),
    )


def test_matched_requires_active_lease_and_owned_evidence():
    entry = reconcile_service(service_id="conport", lease_verdict="ACTIVE", ownership=_owned_evidence())
    assert entry.status == ReconcileStatus.MATCHED


def test_active_lease_without_owned_evidence_is_ambiguous_not_matched():
    entry = reconcile_service(service_id="conport", lease_verdict="ACTIVE", ownership=None)
    assert entry.status == ReconcileStatus.AMBIGUOUS


def test_missing_when_no_lease_and_no_legacy_record():
    entry = reconcile_service(service_id="conport", lease_verdict="UNKNOWN")
    assert entry.status == ReconcileStatus.MISSING


def test_legacy_unbound_when_unmigrated_legacy_record_present():
    entry = reconcile_service(
        service_id="conport", lease_verdict="UNKNOWN", has_legacy_unmigrated_record=True
    )
    assert entry.status == ReconcileStatus.LEGACY_UNBOUND


def test_stale_lease_status():
    entry = reconcile_service(service_id="conport", lease_verdict="STALE")
    assert entry.status == ReconcileStatus.STALE


def test_foreign_for_wrong_project_wrong_instance_or_conflicting():
    for verdict in ("WRONG_PROJECT", "WRONG_INSTANCE", "CONFLICTING"):
        entry = reconcile_service(service_id="conport", lease_verdict=verdict)
        assert entry.status == ReconcileStatus.FOREIGN, verdict


def test_all_six_statuses_are_reachable():
    reached = {
        reconcile_service(service_id="a", lease_verdict="ACTIVE", ownership=_owned_evidence()).status,
        reconcile_service(service_id="b", lease_verdict="UNKNOWN").status,
        reconcile_service(service_id="c", lease_verdict="WRONG_PROJECT").status,
        reconcile_service(service_id="d", lease_verdict="ACTIVE", ownership=None).status,
        reconcile_service(service_id="e", lease_verdict="STALE").status,
        reconcile_service(service_id="f", lease_verdict="UNKNOWN", has_legacy_unmigrated_record=True).status,
    }
    assert reached == set(ReconcileStatus)


def test_reconcile_service_never_mutates_anything():
    """There is no executor: reconcile_service is a pure function with no
    filesystem, network, or subprocess side effects -- calling it twice with
    identical inputs must yield equal (not just equal-shaped) results."""

    a = reconcile_service(service_id="conport", lease_verdict="ACTIVE", ownership=_owned_evidence())
    b = reconcile_service(service_id="conport", lease_verdict="ACTIVE", ownership=_owned_evidence())
    assert a == b


def test_report_by_status_filters():
    from dopemux.mcp.reconcile import ReconcileReport

    entries = (
        reconcile_service(service_id="a", lease_verdict="ACTIVE", ownership=_owned_evidence()),
        reconcile_service(service_id="b", lease_verdict="UNKNOWN"),
    )
    report = ReconcileReport(project_id="p", workspace_id="w", instance_id="i", entries=entries)
    assert [e.service_id for e in report.by_status(ReconcileStatus.MATCHED)] == ["a"]
    assert [e.service_id for e in report.by_status(ReconcileStatus.MISSING)] == ["b"]
