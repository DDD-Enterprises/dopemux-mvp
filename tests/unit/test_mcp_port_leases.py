"""Tests for port lease registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.mcp.port_leases import (
    LeaseRegistryError,
    PortLease,
    PortLeaseRegistry,
    make_lease_id,
)


def test_make_lease_id_stable():
    a = make_lease_id(
        project_slug="dNh_CRM",
        worktree_hash="8d6d",
        service="conport",
        port_role="http",
        port=3040,
    )
    b = make_lease_id(
        project_slug="dNh_CRM",
        worktree_hash="8d6d",
        service="conport",
        port_role="http",
        port=3040,
    )
    assert a == b
    assert "3040" in a


def test_registry_missing(tmp_path: Path):
    reg = PortLeaseRegistry.load(tmp_path / "port-leases.json")
    assert reg.parse_status == "MISSING"
    assert reg.active_leases() == []


def test_atomic_upsert_and_reload(tmp_path: Path):
    path = tmp_path / "port-leases.json"
    reg = PortLeaseRegistry.load(path, create_missing=True)
    lease = PortLease(
        lease_id="lease_test_conport_http_3040",
        port=3040,
        service="conport",
        port_role="http",
        port_var="CONPORT_HTTP_PORT",
        worktree_root="/tmp/wt",
        project_root="/tmp/proj",
        worktree_hash="abcd",
        status="active",
    )
    reg.upsert_lease(lease)
    reg.save()

    reg2 = PortLeaseRegistry.load(path)
    assert reg2.parse_status == "OK"
    assert len(reg2.active_leases()) == 1
    assert reg2.find_active_by_port(3040)["service"] == "conport"


def test_identity_match_and_foreign(tmp_path: Path):
    path = tmp_path / "leases.json"
    reg = PortLeaseRegistry.load(path, create_missing=True)
    reg.upsert_lease(
        PortLease(
            lease_id="l1",
            port=3050,
            service="dope-memory",
            port_role="http",
            worktree_root="/a",
            worktree_hash="aaaa",
            status="active",
        )
    )
    reg.save()
    foreign = reg.find_active_by_port(3050)
    assert foreign is not None
    assert reg.identity_matches(
        foreign, worktree_root="/a", project_root="/p", worktree_hash="aaaa"
    )
    assert not reg.identity_matches(
        foreign, worktree_root="/b", project_root="/p", worktree_hash="bbbb"
    )


def test_parse_error_blocks_save(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    reg = PortLeaseRegistry.load(path)
    assert reg.parse_status == "ERROR"
    with pytest.raises(LeaseRegistryError):
        reg.save()


def test_release(tmp_path: Path):
    path = tmp_path / "leases.json"
    reg = PortLeaseRegistry.load(path, create_missing=True)
    reg.upsert_lease(
        PortLease(
            lease_id="l1",
            port=3060,
            service="conport",
            port_role="sse",
            worktree_root="/w",
            status="active",
        )
    )
    n = reg.mark_released(port=3060)
    assert n == 1
    assert reg.active_leases() == []


def test_project_scoped_upsert_dedupes_across_worktrees(tmp_path: Path):
    path = tmp_path / "leases.json"
    reg = PortLeaseRegistry.load(path, create_missing=True)
    reg.upsert_lease(
        PortLease(
            lease_id="to_wt_a",
            port=7890,
            service="task-orchestrator",
            port_role="http",
            worktree_root="/proj/wt-a",
            project_root="/proj",
            scope="project",
            status="active",
        )
    )
    reg.upsert_lease(
        PortLease(
            lease_id="to_wt_b",
            port=7890,
            service="task-orchestrator",
            port_role="http",
            worktree_root="/proj/wt-b",
            project_root="/proj",
            scope="project",
            status="active",
        )
    )
    active = [
        L
        for L in reg.active_leases()
        if L.get("service") == "task-orchestrator" and L.get("scope") == "project"
    ]
    assert len(active) == 1
    assert active[0]["worktree_root"] == "/proj/wt-b"


def test_find_active_for_identity_separates_scopes(tmp_path: Path):
    path = tmp_path / "leases.json"
    reg = PortLeaseRegistry.load(path, create_missing=True)
    reg.upsert_lease(
        PortLease(
            lease_id="proj",
            port=7890,
            service="task-orchestrator",
            port_role="http",
            worktree_root="/proj/wt-a",
            project_root="/proj",
            worktree_hash="aaaa",
            scope="project",
            status="active",
        )
    )
    reg.upsert_lease(
        PortLease(
            lease_id="wt",
            port=3040,
            service="dope-memory",
            port_role="http",
            worktree_root="/proj/wt-a",
            project_root="/proj",
            worktree_hash="aaaa",
            scope="worktree",
            status="active",
        )
    )
    # Worktree lookup must not return project-scoped lease
    assert (
        reg.find_active_for_identity(
            service="task-orchestrator",
            port_role="http",
            worktree_root="/proj/wt-a",
            worktree_hash="aaaa",
        )
        is None
    )
    # Project lookup returns project lease
    found = reg.find_active_for_identity(
        service="task-orchestrator",
        port_role="http",
        project_root="/proj",
    )
    assert found is not None
    assert found["port"] == 7890
    # Worktree lookup returns worktree lease
    found_wt = reg.find_active_for_identity(
        service="dope-memory",
        port_role="http",
        worktree_root="/proj/wt-a",
        worktree_hash="aaaa",
    )
    assert found_wt is not None
    assert found_wt["port"] == 3040


def test_reconcile_releases_invalid_singleton_lease(tmp_path: Path):
    path = tmp_path / "leases.json"
    reg = PortLeaseRegistry.load(path, create_missing=True)
    reg.upsert_lease(
        PortLease(
            lease_id="lease_project_a_to_7890",
            port=7890,
            service="task-orchestrator",
            port_role="http",
            project_root="/Users/alice/code/project-a",
            worktree_root="/Users/alice/code/project-a",
            status="active",
        )
    )
    reg.save()
    plan = reg.reconcile_reserved_singleton_leases({7890: "task-orchestrator"}, dry_run=True)
    assert plan["invalid_count"] == 1
    assert plan["applied"] is False
    applied = reg.reconcile_reserved_singleton_leases({7890: "task-orchestrator"}, dry_run=False)
    assert applied["applied"] is True
    reg2 = PortLeaseRegistry.load(path)
    assert not any(int(L.get("port") or 0) == 7890 for L in reg2.active_leases())


def test_pytest_defaults_away_from_home_registry(monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", raising=False)
    monkeypatch.delenv("DOPEMUX_ALLOW_HOME_LEASE_REGISTRY", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/unit/test_mcp_port_leases.py::test_x (call)")
    from dopemux.mcp import port_leases as pl

    path = pl.default_lease_registry_path()
    assert "dopemux-mcp-tests" in str(path)
    assert path.name == "port-leases.json"
    assert str(Path.home() / ".dopemux") not in str(path)


def test_parallel_workers_resolve_different_paths(monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", raising=False)
    monkeypatch.delenv("DOPEMUX_ALLOW_HOME_LEASE_REGISTRY", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/unit/test_mcp_port_leases.py::test_parallel (call)")
    from dopemux.mcp import port_leases as pl

    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    p0 = pl.default_lease_registry_path()
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw1")
    p1 = pl.default_lease_registry_path()
    assert p0 != p1
    assert "gw0" in str(p0)
    assert "gw1" in str(p1)


def test_different_pids_resolve_different_paths(monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", raising=False)
    monkeypatch.delenv("DOPEMUX_ALLOW_HOME_LEASE_REGISTRY", raising=False)
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/unit/test_mcp_port_leases.py::test_pid (call)")
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    from dopemux.mcp import port_leases as pl

    monkeypatch.setattr(pl.os, "getpid", lambda: 11111)
    p_a = pl.default_lease_registry_path()
    monkeypatch.setattr(pl.os, "getpid", lambda: 22222)
    p_b = pl.default_lease_registry_path()
    assert p_a != p_b
    assert "11111" in str(p_a)
    assert "22222" in str(p_b)


def test_production_default_is_home_registry(monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", raising=False)
    monkeypatch.delenv("DOPEMUX_ALLOW_HOME_LEASE_REGISTRY", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    from dopemux.mcp import port_leases as pl

    path = pl.default_lease_registry_path()
    assert path == (Path.home() / ".dopemux/mcp/runtime/port-leases.json").resolve()


def test_env_override_wins_over_pytest(monkeypatch, tmp_path: Path):
    custom = tmp_path / "custom-leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(custom))
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/unit/test_mcp_port_leases.py::test_env (call)")
    from dopemux.mcp import port_leases as pl

    assert pl.default_lease_registry_path() == custom.resolve()


def test_two_tmp_path_registries_do_not_share_leases(tmp_path: Path):
    a = tmp_path / "a" / "leases.json"
    b = tmp_path / "b" / "leases.json"
    ra = PortLeaseRegistry.load(a, create_missing=True)
    rb = PortLeaseRegistry.load(b, create_missing=True)
    ra.upsert_lease(
        PortLease(
            lease_id="la",
            port=3100,
            service="conport",
            port_role="sse",
            worktree_root="/a",
            status="active",
        )
    )
    ra.save()
    assert ra.find_active_by_port(3100) is not None
    assert rb.find_active_by_port(3100) is None
    rb2 = PortLeaseRegistry.load(b)
    assert rb2.find_active_by_port(3100) is None
