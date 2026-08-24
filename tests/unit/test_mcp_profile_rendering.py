"""Deterministic profile rendering tests (ADR-DMX-MCPPROF-001)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dopemux.mcp import fleet_catalog, profile_policy


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalog() -> dict:
    return fleet_catalog.load_root_catalog(REPO_ROOT)


def test_deterministic_generation_twice_byte_identical(catalog, tmp_path):
    a = fleet_catalog.generate_profile_output_files(
        catalog, "core-code", repo_root=REPO_ROOT
    )
    b = fleet_catalog.generate_profile_output_files(
        catalog, "core-code", repo_root=REPO_ROOT
    )
    assert a.keys() == b.keys()
    for key in a:
        assert a[key] == b[key], f"non-deterministic output for {key}"


def test_profile_generation_never_includes_all_servers(catalog):
    outputs = fleet_catalog.generate_profile_output_files(
        catalog, "core-code", repo_root=REPO_ROOT
    )
    inv = profile_policy.resolve_profile(
        catalog, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    all_servers = set(catalog["servers"])
    # Profile must be a strict subset for this catalog (many specialized servers exist).
    assert set(inv.selected_servers) < all_servers
    assert "desktop-commander" not in inv.selected_servers
    assert "playwright-mcp" not in inv.selected_servers
    # Generated mcpServers keys ⊆ selected
    import json

    payload = json.loads(outputs["profiles/core-code/mcpServers.json"])
    assert set(payload["mcpServers"]) <= set(inv.selected_servers)
    assert payload["profile"] == "core-code"
    assert payload["profile_digest"] == inv.profile_digest


def test_core_retrieval_excludes_serena_includes_dope_context(catalog):
    inv = profile_policy.resolve_profile(
        catalog, "core-retrieval", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    assert "dope-context" in inv.selected_servers
    assert "serena" not in inv.selected_servers


def test_ui_audit_includes_playwright(catalog):
    inv = profile_policy.resolve_profile(
        catalog, "ui-audit", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    assert "playwright-mcp" in inv.selected_servers


def test_agent_matrix_generate_still_deterministic(catalog):
    a = fleet_catalog.generate_fleet_output_files(catalog)
    b = fleet_catalog.generate_fleet_output_files(catalog)
    assert a == b
