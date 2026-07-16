"""Tests for legacy envrc → lease migration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from dopemux.mcp.lease_migration import migrate_envrc_to_leases
from dopemux.mcp.port_leases import PortLeaseRegistry


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["dope-memory"]},
        "servers": {
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
                "management_model": "compose-service",
            }
        },
    }


def test_migrate_missing_envrc(tmp_path: Path, monkeypatch):
    reg = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg))
    report = migrate_envrc_to_leases(
        tmp_path,
        _catalog(),
        registry_path=reg,
        persist=True,
        is_free_fn=lambda p: True,
    )
    assert report["status"] in {"ASSIGNED", "REUSED", "REBIND"}
    assert "DOPE_MEMORY_PORT" in report["ports"]


def test_migrate_existing_envrc_preferred(tmp_path: Path, monkeypatch):
    reg = tmp_path / "leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(reg))
    (tmp_path / ".envrc.dopemux-mcp").write_text(
        "export DOPE_MEMORY_PORT=3033\nexport DOPEMUX_WORKSPACE_ID=/x\n"
    )
    report = migrate_envrc_to_leases(
        tmp_path,
        _catalog(),
        registry_path=reg,
        persist=True,
        is_free_fn=lambda p: True,
    )
    # Preferred 3033 if free
    assert report["ports"]["DOPE_MEMORY_PORT"] == 3033
    assert any(
        w.get("code") == "LEGACY_HASH_ALLOCATOR_MIGRATED" for w in report["warnings"]
    )
    loaded = PortLeaseRegistry.load(reg)
    assert any(int(L["port"]) == 3033 for L in loaded.active_leases())
