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
