"""Tests for MCP runtime registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.mcp.runtime_registry import (
    RegistryError,
    RuntimeRegistry,
    build_instance_record,
    empty_registry,
)


def test_load_missing(tmp_path: Path):
    path = tmp_path / "instances.json"
    reg = RuntimeRegistry.load(path)
    assert reg.present is False
    assert reg.parse_status == "MISSING"
    assert reg.instances() == []


def test_atomic_write_and_reload(tmp_path: Path):
    path = tmp_path / "instances.json"
    reg = RuntimeRegistry.load(path)
    assert reg.parse_status == "MISSING"
    reg.parse_status = "OK"
    rec = build_instance_record(
        instance_id="proj-abcd-conport",
        project_id="proj",
        workspace_id="/tmp/proj",
        project_root="/tmp/proj",
        worktree_root="/tmp/proj",
        worktree_hash="abcd",
        project_hash="hashhash",
        service="conport",
        scope="worktree",
        status="running",
        ports={"sse": 3041},
        urls={"sse": "http://localhost:3041/sse"},
        container_names=["dopemux-proj-abcd-conport"],
        compose_project_name="dopemux_proj_abcd",
        labels={"dopemux.managed": "true", "dopemux.project_id": "proj"},
    )
    reg.upsert_instance(rec)
    reg.path = path
    reg.save()
    assert path.exists()
    reloaded = RuntimeRegistry.load(path)
    assert reloaded.parse_status == "OK"
    assert len(reloaded.instances()) == 1
    assert reloaded.instances()[0]["service"] == "conport"


def test_parse_error_blocks_save(tmp_path: Path):
    path = tmp_path / "instances.json"
    path.write_text("{not-json")
    reg = RuntimeRegistry.load(path)
    assert reg.parse_status == "ERROR"
    with pytest.raises(RegistryError):
        reg.upsert_instance({"instance_id": "x"})


def test_mark_stopped(tmp_path: Path):
    path = tmp_path / "instances.json"
    reg = RuntimeRegistry(path=path, data=empty_registry(), present=True, parse_status="OK")
    reg.upsert_instance(
        build_instance_record(
            instance_id="p-1-conport",
            project_id="p",
            workspace_id="/p",
            project_root="/p",
            worktree_root="/p",
            worktree_hash="1",
            project_hash="h",
            service="conport",
            scope="worktree",
            status="running",
            ports={},
            urls={},
            container_names=["c"],
            compose_project_name="n",
            labels={},
        )
    )
    n = reg.mark_stopped(project_id="p", service="conport")
    assert n == 1
    assert reg.instances()[0]["status"] == "stopped"
    reg.save()
    data = json.loads(path.read_text())
    assert data["instances"][0]["status"] == "stopped"


def test_find_filters(tmp_path: Path):
    reg = RuntimeRegistry(path=tmp_path / "r.json", data=empty_registry(), parse_status="OK")
    for svc in ("conport", "dope-memory"):
        reg.upsert_instance(
            build_instance_record(
                instance_id=f"p-1-{svc}",
                project_id="p",
                workspace_id="/p",
                project_root="/p",
                worktree_root="/p",
                worktree_hash="1",
                project_hash="h",
                service=svc,
                scope="worktree",
                status="running",
                ports={},
                urls={},
                container_names=[svc],
                compose_project_name="n",
                labels={},
            )
        )
    assert len(reg.find(project_id="p")) == 2
    assert len(reg.find(project_id="p", service="conport")) == 1


def test_prune_stale_dry_run(tmp_path: Path):
    reg = RuntimeRegistry(path=tmp_path / "r.json", data=empty_registry(), parse_status="OK")
    reg.upsert_instance(
        build_instance_record(
            instance_id="keep",
            project_id="p",
            workspace_id="/p",
            project_root="/p",
            worktree_root="/p",
            worktree_hash="1",
            project_hash="h",
            service="conport",
            scope="worktree",
            status="running",
            ports={},
            urls={},
            container_names=["c"],
            compose_project_name="n",
            labels={},
        )
    )
    reg.upsert_instance(
        build_instance_record(
            instance_id="stale",
            project_id="p",
            workspace_id="/p",
            project_root="/p",
            worktree_root="/p",
            worktree_hash="1",
            project_hash="h",
            service="dope-memory",
            scope="worktree",
            status="running",
            ports={},
            urls={},
            container_names=["d"],
            compose_project_name="n",
            labels={},
        )
    )
    assert reg.prune_stale_dry_run(["keep"]) == ["stale"]


def test_env_override(monkeypatch, tmp_path: Path):
    path = tmp_path / "custom.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(path))
    from dopemux.mcp import runtime_registry as rr

    assert rr.default_registry_path() == path.resolve()


def test_p1_service_lease_store_is_independent_of_runtime_registry(monkeypatch, tmp_path: Path):
    """P1's service-lease-v2 store (service_leases.py) must never share a
    path or default env var with this v1 operational runtime registry -- the
    two are independent stores with independent schemas."""

    from dopemux.mcp import runtime_registry as rr
    from dopemux.mcp import service_leases

    assert service_leases.REGISTRY_ENV != rr.REGISTRY_ENV
    assert service_leases.DEFAULT_RELATIVE != rr.DEFAULT_RELATIVE

    monkeypatch.delenv(rr.REGISTRY_ENV, raising=False)
    monkeypatch.delenv(service_leases.REGISTRY_ENV, raising=False)
    assert rr.default_registry_path() != service_leases.default_registry_path()


# --- registry reconcile (stale running instances) -------------------------------------


def _stale_registry(tmp_path: Path) -> RuntimeRegistry:
    """Registry with running+present, running+absent, stopped+absent, running+no-containers."""
    path = tmp_path / "instances.json"
    reg = RuntimeRegistry(path=path, data=empty_registry(), present=True, parse_status="OK")
    specs = [
        ("present-running", "running", ["c-present"]),
        ("absent-running", "running", ["c-absent"]),
        ("absent-stopped", "stopped", ["c-absent"]),
        ("empty-running", "running", []),
    ]
    for iid, status, names in specs:
        rec = build_instance_record(
            instance_id=iid,
            project_id="p",
            workspace_id="/p",
            project_root="/p",
            worktree_root="/p/wt",
            worktree_hash="1",
            project_hash="h",
            service="task-orchestrator",
            scope="worktree",
            status=status,
            ports={"http": 7890},
            urls={},
            container_names=names,
            compose_project_name="n",
            labels={"k": "v"},
        )
        rec["custom_extra"] = {"keep": iid}
        reg.upsert_instance(rec)
    reg.save()
    return reg


def _stale_ids(items) -> list:
    return sorted(i["instance_id"] for i in items)


def test_find_stale_running_detection(tmp_path: Path):
    reg = _stale_registry(tmp_path)
    stale = reg.find_stale_running({"c-present"})
    assert _stale_ids(stale) == ["absent-running", "empty-running"]


def test_find_stale_running_all_present(tmp_path: Path):
    reg = _stale_registry(tmp_path)
    stale = reg.find_stale_running(["c-present", "c-absent"])
    assert _stale_ids(stale) == ["empty-running"]


def test_reconcile_dry_run_writes_nothing(tmp_path: Path):
    reg = _stale_registry(tmp_path)
    before = reg.path.read_bytes()
    plan = reg.reconcile_stale_running({"c-present"}, dry_run=True)
    assert plan["dry_run"] is True
    assert plan["applied"] is False
    assert plan["backup_path"] is None
    assert plan["stale_count"] == 2
    assert _stale_ids(plan["stale"]) == ["absent-running", "empty-running"]
    for key in (
        "instance_id",
        "service",
        "project_root",
        "worktree_root",
        "container_names",
        "updated_at",
    ):
        assert key in plan["stale"][0]
    assert reg.path.read_bytes() == before
    assert list(tmp_path.glob("instances.json.backup-*")) == []


def test_reconcile_apply_backs_up_and_marks_only_stale(tmp_path: Path):
    reg = _stale_registry(tmp_path)
    before = reg.path.read_bytes()
    original = {i["instance_id"]: dict(i) for i in reg.instances()}

    plan = reg.reconcile_stale_running({"c-present"}, dry_run=False)
    assert plan["applied"] is True
    assert plan["stale_count"] == 2
    backups = list(tmp_path.glob("instances.json.backup-*"))
    assert len(backups) == 1
    assert plan["backup_path"] == str(backups[0])
    assert backups[0].read_bytes() == before

    after = {i["instance_id"]: i for i in RuntimeRegistry.load(reg.path).instances()}
    assert set(after) == set(original)  # never removes entries
    for iid in ("absent-running", "empty-running"):
        inst = after[iid]
        assert inst["status"] == "stopped"
        probe = inst["last_probe"]
        assert probe["status"] == "NOT_RUNNING"
        assert probe["source"] == "mcp registry reconcile"
        assert probe["checked_at"] == inst["updated_at"]
        for key, value in original[iid].items():
            if key not in {"status", "updated_at", "last_probe"}:
                assert inst[key] == value
    for iid in ("present-running", "absent-stopped"):
        assert after[iid] == original[iid]


def test_reconcile_apply_second_run_is_noop(tmp_path: Path):
    reg = _stale_registry(tmp_path)
    reg.reconcile_stale_running({"c-present"}, dry_run=False)
    again = reg.reconcile_stale_running({"c-present"}, dry_run=False)
    assert again["stale_count"] == 0
    assert again["applied"] is False
    assert again["backup_path"] is None
    assert len(list(tmp_path.glob("instances.json.backup-*"))) == 1


def test_reconcile_blocked_on_parse_error(tmp_path: Path):
    path = tmp_path / "instances.json"
    path.write_text("{not-json")
    reg = RuntimeRegistry.load(path)
    assert reg.parse_status == "ERROR"
    with pytest.raises(RegistryError):
        reg.reconcile_stale_running(set(), dry_run=False)
    with pytest.raises(RegistryError):
        reg.reconcile_stale_running(set(), dry_run=True)
    assert path.read_text() == "{not-json"
    assert list(tmp_path.glob("instances.json.backup-*")) == []
