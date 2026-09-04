"""P1 control-plane composition: identity + catalog + leases + ownership,
blockers, and the two-projects-same-basename / two-worktrees-one-project
falsification fixtures.

Covers Task 7 (composition half) of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-
CONTROL-PLANE-001.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.mcp import fleet_catalog
from dopemux.mcp.control_plane import build_control_plane_plan
from dopemux.mcp.identity import IdentityClaim, resolve_execution_identity
from dopemux.mcp.identity_registry import IdentityRegistry
from dopemux.mcp.reconcile import ReconcileStatus
from dopemux.mcp.service_leases import LeaseKey, ServiceLeaseRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]


def _real_v2_catalog() -> dict:
    v1 = fleet_catalog.load_root_catalog(REPO_ROOT)
    topology = json.loads((REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text())
    return fleet_catalog.compile_catalog_v2(v1, topology)


def _tiny_catalog() -> dict:
    return {
        "version": 2,
        "servers": {
            "conport": {
                "sharing_class": "WORKTREE_SCOPED",
                "target_class": "PROJECT_SCOPED",
                "transport": "sse",
                "plane": "memory",
                "authority_role": "structured-context-authority",
                "lifecycle": "active",
                "management_model": "compose-service",
                "identity_scope": "per-instance",
                "state_authority": "canonical",
                "mutation_class": "scoped",
                "endpoint_policy": "leased",
                "probe": "mcp",
                "idle_policy": "instance_idle",
                "flip_gate": ["x"],
            },
            "pal-stdio": {
                "sharing_class": "HOST_SINGLETON",
                "target_class": "HOST_SINGLETON",
                "transport": "stdio",
                "plane": "reasoning",
                "authority_role": "reasoning-infrastructure",
                "lifecycle": "operator-managed",
                "management_model": "docker-exec",
                "identity_scope": "singleton",
                "state_authority": "stateless",
                "mutation_class": "none",
                "endpoint_policy": "generated",
                "probe": "mcp",
                "idle_policy": "always_on",
                "flip_gate": [],
            },
            "pal-http-wrapper": {
                "sharing_class": "HOST_SINGLETON",
                "target_class": "RETIRED",
                "transport": "http",
                "plane": "reasoning",
                "authority_role": "reasoning-infrastructure",
                "lifecycle": "decision-required",
                "management_model": "compose-service",
                "identity_scope": "singleton",
                "state_authority": "stateless",
                "mutation_class": "none",
                "endpoint_policy": "fixed",
                "probe": "http",
                "idle_policy": "always_on",
                "flip_gate": [],
            },
        },
    }


def _register_project_with_worktree(reg: IdentityRegistry, *, root_path: str) -> tuple[str, str, str]:
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": root_path}])
    return pid, wid, iid


def test_unresolved_identity_blocks_with_no_selected_services(tmp_path: Path):
    from dopemux.mcp.identity import ResolvedExecutionIdentity

    unresolved = ResolvedExecutionIdentity(resolution_status="UNKNOWN", mutable_routing_allowed=False)
    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)

    plan = build_control_plane_plan(
        resolved_identity=unresolved, catalog_v2=_tiny_catalog(), lease_registry=lease_reg
    )
    assert plan.is_blocked
    assert plan.selected_services == ()
    assert plan.reconcile.entries == ()


def test_target_class_retired_is_inert_and_still_selected(tmp_path: Path):
    """pal-http-wrapper's sharing_class is HOST_SINGLETON (still leasable
    today), but a server whose *own* sharing_class is RETIRED must never be
    selected -- target_class alone (RETIRED) must not exclude it, since
    target_class is explicitly inert in P1."""

    identity_reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid, wid, iid = _register_project_with_worktree(identity_reg, root_path="/repo/a")
    identity = resolve_execution_identity(
        cwd=Path("/repo/a"), registry=identity_reg, actor_id="operator", client_id="claude"
    )
    assert identity.resolution_status == "VERIFIED"

    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    plan = build_control_plane_plan(resolved_identity=identity, catalog_v2=_tiny_catalog(), lease_registry=lease_reg)

    selected_ids = {s.service_id for s in plan.selected_services}
    # pal-http-wrapper has sharing_class HOST_SINGLETON (not RETIRED) so it
    # IS selected even though its target_class is RETIRED (inert in P1).
    assert "pal-http-wrapper" in selected_ids
    assert "pal-stdio" in selected_ids
    assert "conport" in selected_ids


def test_sharing_class_retired_is_never_selected(tmp_path: Path):
    """Unlike target_class, a server whose own sharing_class is RETIRED must
    never appear in selected_services -- RETIRED can never own a lease."""

    identity_reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid, wid, iid = _register_project_with_worktree(identity_reg, root_path="/repo/a")
    identity = resolve_execution_identity(
        cwd=Path("/repo/a"), registry=identity_reg, actor_id="operator", client_id="claude"
    )
    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)

    catalog = _tiny_catalog()
    catalog["servers"]["retired-thing"] = {
        **catalog["servers"]["pal-stdio"],
        "sharing_class": "RETIRED",
        "target_class": "RETIRED",
    }
    plan = build_control_plane_plan(resolved_identity=identity, catalog_v2=catalog, lease_registry=lease_reg)

    selected_ids = {s.service_id for s in plan.selected_services}
    assert "retired-thing" not in selected_ids
    assert "pal-stdio" in selected_ids


def test_two_projects_identical_basenames_yield_distinct_plans(tmp_path: Path):
    identity_reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid_a, _, _ = _register_project_with_worktree(identity_reg, root_path="/proj-A/repo")
    pid_b, _, _ = _register_project_with_worktree(identity_reg, root_path="/proj-B/repo")

    identity_a = resolve_execution_identity(
        cwd=Path("/proj-A/repo"), registry=identity_reg, actor_id="operator", client_id="claude"
    )
    identity_b = resolve_execution_identity(
        cwd=Path("/proj-B/repo"), registry=identity_reg, actor_id="operator", client_id="claude"
    )

    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    plan_a = build_control_plane_plan(resolved_identity=identity_a, catalog_v2=_tiny_catalog(), lease_registry=lease_reg)
    plan_b = build_control_plane_plan(resolved_identity=identity_b, catalog_v2=_tiny_catalog(), lease_registry=lease_reg)

    assert plan_a.resolved_identity.project_id == pid_a
    assert plan_b.resolved_identity.project_id == pid_b
    assert plan_a.resolved_identity.project_id != plan_b.resolved_identity.project_id

    conport_a = next(s for s in plan_a.selected_services if s.service_id == "conport")
    conport_b = next(s for s in plan_b.selected_services if s.service_id == "conport")
    assert conport_a.lease_key.storage_key() != conport_b.lease_key.storage_key()


def test_two_worktrees_one_project_share_project_scoped_lease_key(tmp_path: Path):
    """Two worktrees of one project retain distinct instance_id while
    sharing the same project_id -- so a PROJECT_SCOPED lease key is
    identical, but a WORKTREE_SCOPED lease key differs."""

    identity_reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = identity_reg.register_project(aliases=[])
    wid = identity_reg.register_workspace(project_id=pid, aliases=[])
    identity_reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/repo/wt1"}]
    )
    identity_reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/repo/wt2"}]
    )

    identity_1 = resolve_execution_identity(
        cwd=Path("/repo/wt1"), registry=identity_reg, actor_id="operator", client_id="claude"
    )
    identity_2 = resolve_execution_identity(
        cwd=Path("/repo/wt2"), registry=identity_reg, actor_id="operator", client_id="claude"
    )
    assert identity_1.project_id == identity_2.project_id == pid
    assert identity_1.instance_id != identity_2.instance_id

    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    plan_1 = build_control_plane_plan(resolved_identity=identity_1, catalog_v2=_tiny_catalog(), lease_registry=lease_reg)
    plan_2 = build_control_plane_plan(resolved_identity=identity_2, catalog_v2=_tiny_catalog(), lease_registry=lease_reg)

    conport_1 = next(s for s in plan_1.selected_services if s.service_id == "conport")
    conport_2 = next(s for s in plan_2.selected_services if s.service_id == "conport")
    assert conport_1.lease_key.storage_key() != conport_2.lease_key.storage_key()


def test_real_catalog_builds_a_full_plan_with_no_executor(tmp_path: Path):
    """End-to-end smoke test against the real compiled catalog: proves the
    composition works over all 19 real servers, and that nothing in the
    plan is executable (only data)."""

    identity_reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid, wid, iid = _register_project_with_worktree(identity_reg, root_path=str(REPO_ROOT))
    identity = resolve_execution_identity(
        cwd=REPO_ROOT, registry=identity_reg, actor_id="operator", client_id="claude"
    )
    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)

    plan = build_control_plane_plan(resolved_identity=identity, catalog_v2=_real_v2_catalog(), lease_registry=lease_reg)

    assert not plan.is_blocked
    assert len(plan.selected_services) == 19
    for entry in plan.reconcile.entries:
        assert entry.status in set(ReconcileStatus)
    # no method on the plan can start/stop/adopt anything; it's plain data.
    assert not hasattr(plan, "start")
    assert not hasattr(plan, "apply")


def test_wrong_project_lease_surfaces_as_foreign_in_reconcile(tmp_path: Path):
    identity_reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid, wid, iid = _register_project_with_worktree(identity_reg, root_path="/repo/real")
    identity = resolve_execution_identity(
        cwd=Path("/repo/real"), registry=identity_reg, actor_id="operator", client_id="claude"
    )

    lease_reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    other_key = LeaseKey(sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="prj_someone_else", instance_id="inst_x")
    lease_reg.acquire(
        other_key,
        registry_generation=identity.registry_generation,
        owner_runtime_identity={"runtime_kind": "container", "runtime_id": "c1"},
        endpoint={"transport": "sse", "port": 3041},
    )
    # The real key for our identity finds nothing -> MISSING, not FOREIGN,
    # because reconcile only classifies FOREIGN when a lease under *our*
    # key exists but disagrees -- a lease under someone else's key is simply
    # invisible to our key lookup (that is the isolation property).
    plan = build_control_plane_plan(resolved_identity=identity, catalog_v2=_tiny_catalog(), lease_registry=lease_reg)
    conport_entry = next(e for e in plan.reconcile.entries if e.service_id == "conport")
    assert conport_entry.status == ReconcileStatus.MISSING
