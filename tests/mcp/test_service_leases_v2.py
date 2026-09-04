"""P1 service-lease-v2: endpoint authority, atomic persistence, fail-closed
verdicts, and read-only legacy migration preview.

Covers Task 4 of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001 and the
falsification-contract fixtures FX-LEASE-01..04 at unit-test granularity.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp.service_leases import (
    LeaseKey,
    MigrationPreview,
    ServiceLeaseConflict,
    ServiceLeaseError,
    ServiceLeaseRegistry,
    default_registry_path,
    lease_verdict,
    preview_legacy_migration,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LEASE_SCHEMA = REPO_ROOT / "schemas/mcp/service-lease-v2.schema.json"


def _schema() -> dict:
    return json.loads(LEASE_SCHEMA.read_text())


def _runtime_id(name: str = "container-1") -> dict:
    return {"runtime_kind": "container", "runtime_id": name}


def _endpoint(port: int = 7890) -> dict:
    return {"transport": "http", "host": "127.0.0.1", "port": port}


# ---- LeaseKey shape enforcement -------------------------------------------


def test_host_singleton_key_rejects_tenant_ids():
    with pytest.raises(ServiceLeaseError):
        LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio", project_id="p")


def test_project_scoped_key_requires_project_id():
    with pytest.raises(ServiceLeaseError):
        LeaseKey(sharing_class="PROJECT_SCOPED", service_id="task-orchestrator")


def test_worktree_scoped_key_requires_project_and_instance():
    with pytest.raises(ServiceLeaseError):
        LeaseKey(sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="p")


def test_retired_key_always_rejected():
    with pytest.raises(ServiceLeaseError):
        LeaseKey(sharing_class="RETIRED", service_id="pal-http-wrapper")


def test_project_and_worktree_keys_differ_by_instance():
    a = LeaseKey(sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="p", instance_id="i1")
    b = LeaseKey(sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="p", instance_id="i2")
    assert a.storage_key() != b.storage_key()


# ---- registry persistence + schema conformance -----------------------------


def test_acquire_produces_schema_valid_lease(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="PROJECT_SCOPED", service_id="conport", project_id="prj_a")
    lease = reg.acquire(
        key,
        registry_generation=3,
        owner_runtime_identity=_runtime_id(),
        endpoint=_endpoint(),
    )
    jsonschema.validate(lease.to_schema_dict(), _schema())
    assert lease.owner_epoch == 0
    assert lease.status == "active"

    reloaded = ServiceLeaseRegistry.load(tmp_path / "leases.json")
    assert reloaded.get(key) is not None
    jsonschema.validate(reloaded.get(key).to_schema_dict(), _schema())


def test_acquire_is_idempotent_for_same_owner(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    first = reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())
    second = reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())
    assert first.lease_id == second.lease_id
    assert first.owner_epoch == second.owner_epoch == 0


def test_acquire_conflicting_owner_raises(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id("a"), endpoint=_endpoint())
    with pytest.raises(ServiceLeaseConflict):
        reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id("b"), endpoint=_endpoint())


def test_transfer_bumps_owner_epoch(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    first = reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id("a"), endpoint=_endpoint())
    second = reg.transfer(
        key, registry_generation=1, new_owner_runtime_identity=_runtime_id("b"), endpoint=_endpoint()
    )
    assert second.owner_epoch == first.owner_epoch + 1
    assert second.owner_runtime_identity == _runtime_id("b")


def test_release_and_mark_stale(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())
    released = reg.release(key)
    assert released.status == "released"
    reg2 = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key2 = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-http-wrapper")
    reg2.acquire(key2, registry_generation=1, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())
    staled = reg2.mark_stale(key2)
    assert staled.status == "stale"


def test_parse_error_blocks_mutation(tmp_path: Path):
    path = tmp_path / "leases.json"
    path.write_text("{not-json")
    reg = ServiceLeaseRegistry.load(path)
    assert reg.parse_status == "ERROR"
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    with pytest.raises(ServiceLeaseError):
        reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())


def test_env_override(monkeypatch, tmp_path: Path):
    path = tmp_path / "custom-leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_SERVICE_LEASE_REGISTRY", str(path))
    assert default_registry_path() == path.resolve()


# ---- fail-closed lease_verdict / FX-LEASE fixtures -------------------------


def test_project_lease_reusable_across_worktrees_same_project(tmp_path: Path):
    """Project leases are reusable across worktrees only for the same
    canonical project_id."""

    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="PROJECT_SCOPED", service_id="task-orchestrator", project_id="prj_a")
    lease = reg.acquire(key, registry_generation=5, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())

    # Same project, resolved from a different worktree -> same key, ACTIVE.
    verdict = lease_verdict(lease, key=key, current_registry_generation=5)
    assert verdict == "ACTIVE"


def test_worktree_lease_cannot_cross_instance(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="prj_a", instance_id="inst_1")
    lease = reg.acquire(key, registry_generation=2, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())

    other_instance_key = LeaseKey(
        sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="prj_a", instance_id="inst_2"
    )
    verdict = lease_verdict(lease, key=other_instance_key, current_registry_generation=2)
    assert verdict == "WRONG_INSTANCE"


def test_fx_lease_01_stale_generation_denies(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="WORKTREE_SCOPED", service_id="conport", project_id="prj_a", instance_id="inst_1")
    lease = reg.acquire(key, registry_generation=4, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())

    # Registry has since advanced (e.g. worktree deleted and re-registered).
    verdict = lease_verdict(lease, key=key, current_registry_generation=5)
    assert verdict == "STALE"


def test_fx_lease_02_foreign_owner_denies_even_with_matching_key(tmp_path: Path):
    """A service-family probe may pass, but ownership-identity mismatch
    (foreign process on the leased port) must still deny."""

    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    lease = reg.acquire(
        key, registry_generation=1, owner_runtime_identity=_runtime_id("real-owner"), endpoint=_endpoint()
    )
    verdict = lease_verdict(
        lease, key=key, current_registry_generation=1, expected_owner_runtime_id="foreign-process"
    )
    assert verdict == "CONFLICTING"


def test_fx_lease_03_wrong_project_labels_hard_fails(tmp_path: Path):
    reg = ServiceLeaseRegistry.load(tmp_path / "leases.json", create_missing=True)
    key = LeaseKey(sharing_class="PROJECT_SCOPED", service_id="task-orchestrator", project_id="prj_real")
    lease = reg.acquire(key, registry_generation=1, owner_runtime_identity=_runtime_id(), endpoint=_endpoint())

    wrong_key = LeaseKey(sharing_class="PROJECT_SCOPED", service_id="task-orchestrator", project_id="prj_other")
    verdict = lease_verdict(lease, key=wrong_key, current_registry_generation=1)
    assert verdict == "WRONG_PROJECT"


def test_fx_lease_04_unlabeled_service_has_no_lease_denies(tmp_path: Path):
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="unregistered-service")
    verdict = lease_verdict(None, key=key, current_registry_generation=1)
    assert verdict == "UNKNOWN"


def test_released_lease_denies():
    key = LeaseKey(sharing_class="HOST_SINGLETON", service_id="pal-stdio")
    lease_dict = {
        "schema_version": "dopemux.mcp.service-lease.v2",
        "lease_id": "lease-1",
        "service_id": "pal-stdio",
        "sharing_class": "HOST_SINGLETON",
        "registry_generation": 1,
        "owner_epoch": 0,
        "endpoint": _endpoint(),
        "owner_runtime_identity": _runtime_id(),
        "status": "released",
        "created_at": "2026-09-04T00:00:00Z",
        "updated_at": "2026-09-04T00:00:00Z",
        "last_verified_at": "2026-09-04T00:00:00Z",
        "evidence_refs": [],
    }
    from dopemux.mcp.service_leases import ServiceLease

    lease = ServiceLease.from_schema_dict(lease_dict)
    assert lease_verdict(lease, key=key, current_registry_generation=1) == "RELEASED"


# ---- read-only legacy migration preview ------------------------------------


def test_migration_preview_convertible_project_scope():
    legacy = [
        {
            "lease_id": "l1",
            "service": "conport",
            "scope": "worktree",
            "status": "active",
            "port": 3041,
            "project_id": "legacy-hash-proj",
            "instance_id": "legacy-hash-inst",
        }
    ]
    preview = preview_legacy_migration(legacy)
    assert isinstance(preview, MigrationPreview)
    assert len(preview.convertible) == 1
    assert preview.convertible[0]["target_sharing_class"] == "WORKTREE_SCOPED"
    assert preview.ambiguous == ()
    assert preview.rejected == ()


def test_migration_preview_ambiguous_singleton_with_project_residue():
    legacy = [
        {
            "lease_id": "l2",
            "service": "pal",
            "scope": "singleton",
            "status": "active",
            "port": 3003,
            "project_id": "leftover-hash",
        }
    ]
    preview = preview_legacy_migration(legacy)
    assert len(preview.ambiguous) == 1
    assert preview.convertible == ()


def test_migration_preview_rejects_released_and_malformed():
    legacy = [
        {"lease_id": "l3", "service": "conport", "scope": "worktree", "status": "released", "port": 3041},
        {"lease_id": "l4", "service": "", "scope": "worktree", "status": "active", "port": 0},
    ]
    preview = preview_legacy_migration(legacy)
    assert len(preview.rejected) == 2
    assert preview.convertible == ()


def test_migration_preview_flags_colliding_service_scope():
    legacy = [
        {
            "lease_id": "l5",
            "service": "dope-memory",
            "scope": "worktree",
            "status": "active",
            "port": 3055,
            "project_id": "p1",
            "instance_id": "i1",
        },
        {
            "lease_id": "l6",
            "service": "dope-memory",
            "scope": "worktree",
            "status": "active",
            "port": 3056,
            "project_id": "p2",
            "instance_id": "i2",
        },
    ]
    preview = preview_legacy_migration(legacy)
    assert len(preview.ambiguous) == 2
    assert preview.convertible == ()


def test_migration_preview_never_touches_filesystem(tmp_path: Path, monkeypatch):
    """The preview function only reads the list it's given -- it must never
    reach for the real legacy registry path itself."""

    import dopemux.mcp.port_leases as port_leases

    monkeypatch.setattr(
        port_leases,
        "default_lease_registry_path",
        lambda: (_ for _ in ()).throw(AssertionError("must not touch legacy registry path")),
    )
    preview_legacy_migration([{"lease_id": "l", "service": "x", "scope": "singleton", "status": "active", "port": 1}])
