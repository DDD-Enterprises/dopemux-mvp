"""Tests for lease-aware port allocator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from dopemux.mcp.port_allocator import (
    allocate_ports,
    allocate_ports_map,
    preferred_port_for_path,
    singleton_reserved_ports,
)
from dopemux.mcp.port_leases import PortLease, PortLeaseRegistry


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport", "dope-memory", "task-orchestrator"]},
        "servers": {
            "pal": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3003/mcp",
            },
            "serena": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3006/mcp",
            },
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
                "management_model": "compose-service",
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
                "management_model": "compose-service",
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "per-repo",
                "transport": "http",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
                "management_model": "wrapper-singleton",
            },
        },
    }


def test_preferred_formula_stable(tmp_path: Path):
    a = preferred_port_for_path(str(tmp_path), 3005)
    b = preferred_port_for_path(str(tmp_path), 3005)
    assert a == b
    assert 3005 <= a <= 3104


def test_singleton_reserved_from_catalog():
    r = singleton_reserved_ports(_catalog())
    assert 3003 in r
    assert 3006 in r


def test_assign_preferred_when_free(tmp_path: Path, monkeypatch):
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))

    result = allocate_ports(
        ["conport", "dope-memory", "task-orchestrator"],
        _catalog(),
        worktree=str(tmp_path / "wt"),
        project_root=str(tmp_path / "wt"),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert result.status in {"ASSIGNED", "REUSED", "REBIND"}
    assert "CONPORT_MCP_PORT" in result.ports
    assert "DOPE_MEMORY_PORT" in result.ports
    assert result.ports["TASK_ORCHESTRATOR_HTTP_PORT"] == 7890
    # all ports unique
    assert len(set(result.ports.values())) == len(result.ports)
    # no reserved collision
    assert 3003 not in result.ports.values()
    assert 3006 not in result.ports.values()
    reg = PortLeaseRegistry.load(reg_path)
    assert len(reg.active_leases()) >= 3


def test_rebind_when_preferred_reserved(tmp_path: Path, monkeypatch):
    """Force preferred path onto reserved by mocking preferred via envrc."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    # Prefer reserved singleton port for dope-memory
    result = allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=str(tmp_path / "wt"),
        project_root=str(tmp_path / "wt"),
        existing_envrc={"DOPE_MEMORY_PORT": "3003"},
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert result.ports["DOPE_MEMORY_PORT"] != 3003
    assert any(r.get("preferred") == 3003 for r in result.rebinds) or result.status == "REBIND"


def test_cross_worktree_lease_collision_avoided(tmp_path: Path, monkeypatch):
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    wt_a = tmp_path / "a"
    wt_b = tmp_path / "b"
    wt_a.mkdir()
    wt_b.mkdir()

    r1 = allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=str(wt_a),
        project_root=str(wt_a),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    port_a = r1.ports["DOPE_MEMORY_PORT"]

    # Force B to prefer A's port
    r2 = allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=str(wt_b),
        project_root=str(wt_b),
        existing_envrc={"DOPE_MEMORY_PORT": str(port_a)},
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert r2.ports["DOPE_MEMORY_PORT"] != port_a
    assert r2.status in {"REBIND", "ASSIGNED"}


def test_dry_run_does_not_write(tmp_path: Path, monkeypatch):
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=str(tmp_path),
        registry_path=reg_path,
        persist=False,
        dry_run=True,
        is_free_fn=lambda p: True,
    )
    assert not reg_path.exists() or PortLeaseRegistry.load(reg_path).active_leases() == []


def test_to_reserved_singleton_not_leased(tmp_path: Path, monkeypatch):
    """TO:7890 is reserved singleton — assign env port, never write project lease (006R)."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    cat = _catalog()
    cat["servers"]["task-orchestrator"]["port_policy"] = "reserved_singleton"
    cat["servers"]["task-orchestrator"]["reserved_port"] = 7890

    result = allocate_ports(
        ["task-orchestrator"],
        cat,
        worktree=str(tmp_path),
        project_root=str(tmp_path),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert result.ports["TASK_ORCHESTRATOR_HTTP_PORT"] == 7890
    assert result.status != "BLOCKED"
    assert not any(L.get("port") == 7890 for L in result.leases)
    reg = PortLeaseRegistry.load(reg_path)
    assert not any(int(L.get("port") or 0) == 7890 for L in reg.active_leases())


def test_allocate_ports_map_drop_in(tmp_path: Path, monkeypatch):
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    ports = allocate_ports_map(
        str(tmp_path),
        ["conport"],
        _catalog(),
        project_root=str(tmp_path),
        registry_path=reg_path,
        is_free_fn=lambda p: True,
    )
    assert "CONPORT_MCP_PORT" in ports
    assert "CONPORT_HTTP_PORT" in ports


def test_fixed_port_blocked_when_occupied_unknown(tmp_path: Path, monkeypatch):
    """Fixed port with no foreign lease but a live socket must BLOCK, not lease."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))

    result = allocate_ports(
        ["task-orchestrator"],
        _catalog(),
        worktree=str(tmp_path),
        project_root=str(tmp_path),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: False,  # 7890 occupied by unknown process
    )
    assert result.status == "BLOCKED"
    assert any(b.get("code") == "LEASE_PORT_OCCUPIED" for b in result.blocking_findings)
    # Must not write a lease for the occupied fixed port
    reg = PortLeaseRegistry.load(reg_path)
    assert reg.find_active_by_port(7890) is None


def test_status_reused_on_second_allocation(tmp_path: Path, monkeypatch):
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    wt = str(tmp_path / "wt")
    (tmp_path / "wt").mkdir()

    r1 = allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=wt,
        project_root=wt,
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert r1.status in {"ASSIGNED", "REUSED"}
    port = r1.ports["DOPE_MEMORY_PORT"]

    r2 = allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=wt,
        project_root=wt,
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert r2.ports["DOPE_MEMORY_PORT"] == port
    assert r2.status == "REUSED"


def test_worktree_scoped_does_not_reuse_project_lease(tmp_path: Path, monkeypatch):
    """A worktree-scoped service must not adopt a project-scoped lease slot."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    wt = tmp_path / "wt"
    wt.mkdir()
    proj = str(wt)

    reg = PortLeaseRegistry.load(reg_path, create_missing=True)
    # Malformed/legacy: project-scoped lease for a normally worktree service
    reg.upsert_lease(
        PortLease(
            lease_id="proj_dm",
            port=3099,
            service="dope-memory",
            port_role="http",
            port_var="DOPE_MEMORY_PORT",
            worktree_root=str(wt),
            worktree_hash="dead",
            project_root=proj,
            scope="project",
            status="active",
        )
    )
    reg.save()

    result = allocate_ports(
        ["dope-memory"],
        _catalog(),
        worktree=str(wt),
        project_root=proj,
        existing_envrc={"DOPE_MEMORY_PORT": "3101"},
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert result.ports["DOPE_MEMORY_PORT"] == 3101
    assert not any(
        w.get("code") == "LEASE_REUSED" and w.get("port") == 3099 for w in result.warnings
    )


def _reserved_singleton_catalog() -> Dict[str, Any]:
    """Catalog whose TO entry declares explicit reserved-singleton markers."""
    cat = _catalog()
    cat["servers"]["task-orchestrator"]["port_policy"] = "reserved_singleton"
    cat["servers"]["task-orchestrator"]["reserved_port"] = 7890
    return cat


def test_reserved_singleton_assigned_when_live_singleton_identified(tmp_path: Path, monkeypatch):
    """RUNTIME regression: a healthy live singleton on the reserved port is
    identified via the MCP handshake and ASSIGNED (never leased), not BLOCKED.

    Reproduces the ``dopemux mcp init --force`` fail-closed bug where a healthy
    task-orchestrator on :7890 was permanently unrecognized (it never writes a
    lease, so the lease-only legitimacy check could never succeed).
    """
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))

    result = allocate_ports(
        ["task-orchestrator"],
        _reserved_singleton_catalog(),
        worktree=str(tmp_path),
        project_root=str(tmp_path),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: False,  # :7890 occupied by the live singleton
        singleton_probe_fn=lambda port, path: "mcp-task-orchestrator-current",
    )

    assert result.status != "BLOCKED"
    assert result.ports["TASK_ORCHESTRATOR_HTTP_PORT"] == 7890
    assert any(
        w.get("code") == "ALLOCATOR_RESERVED_SINGLETON_IDENTIFIED" for w in result.warnings
    )
    # A reserved singleton is never written as a lease.
    assert not any(int(L.get("port") or 0) == 7890 for L in result.leases)
    reg = PortLeaseRegistry.load(reg_path)
    assert reg.find_active_by_port(7890) is None


def test_reserved_singleton_blocked_when_identity_mismatch(tmp_path: Path, monkeypatch):
    """Occupied reserved port whose serverInfo.name does NOT match stays fail-closed."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))

    result = allocate_ports(
        ["task-orchestrator"],
        _reserved_singleton_catalog(),
        worktree=str(tmp_path),
        project_root=str(tmp_path),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: False,
        singleton_probe_fn=lambda port, path: "some-other-mcp-server",
    )

    assert result.status == "BLOCKED"
    assert any(b.get("code") == "LEASE_PORT_OCCUPIED" for b in result.blocking_findings)
    reg = PortLeaseRegistry.load(reg_path)
    assert reg.find_active_by_port(7890) is None


def test_reserved_singleton_blocked_when_probe_unreachable(tmp_path: Path, monkeypatch):
    """Occupied reserved port where the identity probe fails (None) stays fail-closed."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))

    result = allocate_ports(
        ["task-orchestrator"],
        _reserved_singleton_catalog(),
        worktree=str(tmp_path),
        project_root=str(tmp_path),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: False,
        singleton_probe_fn=lambda port, path: None,  # unreachable / non-MCP occupant
    )

    assert result.status == "BLOCKED"
    assert any(b.get("code") == "LEASE_PORT_OCCUPIED" for b in result.blocking_findings)


def test_reserved_singleton_free_port_never_probes(tmp_path: Path, monkeypatch):
    """When the reserved port is free, assign without probing (singleton not up yet)."""
    reg_path = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg_path))
    calls: list[int] = []

    def _boom(port: int, path: str):
        calls.append(port)
        raise AssertionError("probe must not run when the reserved port is free")

    result = allocate_ports(
        ["task-orchestrator"],
        _reserved_singleton_catalog(),
        worktree=str(tmp_path),
        project_root=str(tmp_path),
        registry_path=reg_path,
        persist=True,
        is_free_fn=lambda p: True,  # nothing listening on :7890 yet
        singleton_probe_fn=_boom,
    )

    assert calls == []
    assert result.status != "BLOCKED"
    assert result.ports["TASK_ORCHESTRATOR_HTTP_PORT"] == 7890


def test_probe_mcp_server_name_parses_serverinfo():
    """The MCP-handshake probe extracts result.serverInfo.name from a JSON body."""
    from dopemux.mcp.task_orchestrator_identity import probe_mcp_server_name

    captured: Dict[str, Any] = {}

    def _fake_post(url: str, body: bytes, headers: Dict[str, str]) -> bytes:
        captured["url"] = url
        return (
            b'{"jsonrpc":"2.0","id":1,"result":{"serverInfo":'
            b'{"name":"mcp-task-orchestrator-current","version":"3.8.0"}}}'
        )

    name = probe_mcp_server_name(7890, opener=_fake_post)
    assert name == "mcp-task-orchestrator-current"
    assert captured["url"] == "http://127.0.0.1:7890/mcp"


def test_probe_mcp_server_name_fails_closed_on_bad_response():
    """Non-JSON / malformed / error responses return None (fail closed)."""
    from dopemux.mcp.task_orchestrator_identity import probe_mcp_server_name

    def _garbage(url: str, body: bytes, headers: Dict[str, str]) -> bytes:
        return b"not json at all"

    def _raises(url: str, body: bytes, headers: Dict[str, str]) -> bytes:
        raise OSError("connection refused")

    def _no_serverinfo(url: str, body: bytes, headers: Dict[str, str]) -> bytes:
        return b'{"jsonrpc":"2.0","id":1,"result":{}}'

    assert probe_mcp_server_name(7890, opener=_garbage) is None
    assert probe_mcp_server_name(7890, opener=_raises) is None
    assert probe_mcp_server_name(7890, opener=_no_serverinfo) is None
