"""Read-only control-plane composition (P1 fleet control plane).

Composes resolved identity, a compiled catalog-v2, service leases, and
ownership evidence into one ``ControlPlanePlan``. This is a preview/plan
object only: it selects service specs and states blockers, but never
starts, stops, adopts, or migrates anything, and never activates v2
mutation behavior -- see ``04_P1_CONTRACT.md``'s activation boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from dopemux.mcp.identity import ResolvedExecutionIdentity
from dopemux.mcp.ownership import OwnershipEvidence
from dopemux.mcp.reconcile import ReconcileReport, reconcile_service
from dopemux.mcp.service_leases import (
    LeaseKey,
    ServiceLease,
    ServiceLeaseRegistry,
    lease_verdict,
)


class ControlPlaneError(RuntimeError):
    """Raised for a caller/programming error (not a routine blocker, which
    is represented in ``ControlPlanePlan.blockers`` instead)."""


@dataclass(frozen=True)
class SelectedService:
    service_id: str
    sharing_class: str
    lease_key: Optional[LeaseKey]
    lease: Optional[ServiceLease]
    lease_verdict: str


@dataclass(frozen=True)
class ControlPlanePlan:
    resolved_identity: ResolvedExecutionIdentity
    selected_services: Tuple[SelectedService, ...]
    reconcile: ReconcileReport
    materialization_inputs: Optional[Dict[str, Any]]
    blockers: Tuple[str, ...]

    @property
    def is_blocked(self) -> bool:
        return bool(self.blockers)


def _lease_key_for(sharing_class: str, service_id: str, identity: ResolvedExecutionIdentity) -> Optional[LeaseKey]:
    if sharing_class == "RETIRED":
        return None
    if sharing_class == "HOST_SINGLETON":
        return LeaseKey(sharing_class=sharing_class, service_id=service_id)
    if sharing_class == "PROJECT_SCOPED":
        if not identity.project_id:
            return None
        return LeaseKey(sharing_class=sharing_class, service_id=service_id, project_id=identity.project_id)
    if sharing_class == "WORKTREE_SCOPED":
        if not identity.project_id or not identity.instance_id:
            return None
        return LeaseKey(
            sharing_class=sharing_class,
            service_id=service_id,
            project_id=identity.project_id,
            instance_id=identity.instance_id,
        )
    raise ControlPlaneError(f"unknown sharing_class: {sharing_class!r}")


def build_control_plane_plan(
    *,
    resolved_identity: ResolvedExecutionIdentity,
    catalog_v2: Dict[str, Any],
    lease_registry: ServiceLeaseRegistry,
    ownership_by_service: Optional[Dict[str, OwnershipEvidence]] = None,
    legacy_unmigrated_service_ids: frozenset = frozenset(),
) -> ControlPlanePlan:
    """Build a read-only plan for one resolved identity against a compiled
    v2 catalog. ``ownership_by_service`` and ``legacy_unmigrated_service_ids``
    are caller-supplied evidence (this never probes Docker or reads the
    legacy registry itself -- see ``ownership.py``/``service_leases.py``).

    RETIRED-sharing-class servers are never selected. Everything else is
    always *selected* (listed) regardless of reconcile status -- selection
    is inventory, not authorization; only ``reconcile.entries`` states
    whether mutation would ever be appropriate, and none of it executes here.
    """

    blockers = []
    if resolved_identity.resolution_status != "VERIFIED":
        blockers.append(f"identity not VERIFIED: resolution_status={resolved_identity.resolution_status}")
        return ControlPlanePlan(
            resolved_identity=resolved_identity,
            selected_services=(),
            reconcile=ReconcileReport(project_id=None, workspace_id=None, instance_id=None, entries=()),
            materialization_inputs=None,
            blockers=tuple(blockers),
        )

    ownership_by_service = ownership_by_service or {}
    selected: list[SelectedService] = []
    reconcile_entries = []

    for service_id in sorted(catalog_v2.get("servers", {})):
        spec = catalog_v2["servers"][service_id]
        sharing_class = spec.get("sharing_class")
        if sharing_class == "RETIRED":
            continue

        key = _lease_key_for(sharing_class, service_id, resolved_identity)
        if key is None:
            blockers.append(
                f"{service_id}: cannot form a lease key for sharing_class={sharing_class!r} "
                "from the resolved identity"
            )
            continue

        lease = lease_registry.get(key)
        verdict = lease_verdict(
            lease,
            key=key,
            current_registry_generation=resolved_identity.registry_generation,
        )
        selected.append(
            SelectedService(
                service_id=service_id,
                sharing_class=sharing_class,
                lease_key=key,
                lease=lease,
                lease_verdict=verdict,
            )
        )
        reconcile_entries.append(
            reconcile_service(
                service_id=service_id,
                lease_verdict=verdict,
                ownership=ownership_by_service.get(service_id),
                has_legacy_unmigrated_record=service_id in legacy_unmigrated_service_ids,
            )
        )

    report = ReconcileReport(
        project_id=resolved_identity.project_id,
        workspace_id=resolved_identity.workspace_id,
        instance_id=resolved_identity.instance_id,
        entries=tuple(reconcile_entries),
    )

    return ControlPlanePlan(
        resolved_identity=resolved_identity,
        selected_services=tuple(selected),
        reconcile=report,
        materialization_inputs=None,
        blockers=tuple(blockers),
    )
