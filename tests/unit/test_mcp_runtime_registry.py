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
