"""Unit tests for MCP profile_policy (ADR-DMX-MCPPROF-001)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.mcp import fleet_catalog, profile_policy


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalog() -> dict:
    return fleet_catalog.load_root_catalog(REPO_ROOT)


def test_list_profiles_includes_initial_set(catalog):
    names = profile_policy.list_profiles(catalog)
    assert "core-code" in names
    assert "core-retrieval" in names
    assert "ui-audit" in names
    assert "planning-audit" in names
    assert "all" not in names


def test_unknown_profile_fail_closed(catalog):
    with pytest.raises(profile_policy.ProfilePolicyError, match="unknown profile"):
        profile_policy.get_profile(catalog, "does-not-exist")


def test_no_implicit_all(catalog):
    with pytest.raises(profile_policy.ProfilePolicyError, match="forbidden"):
        profile_policy.get_profile(catalog, "all")
    with pytest.raises(profile_policy.ProfilePolicyError, match="forbidden"):
        profile_policy.assert_no_implicit_all("all")
    with pytest.raises(profile_policy.ProfilePolicyError, match="forbidden"):
        profile_policy.resolve_default_profile(catalog, "*")


def test_pal_http_not_selected_as_mcp(catalog):
    # Inject pal into a synthetic profile to prove the filter.
    cat = json.loads(json.dumps(catalog))
    cat["profiles"]["bad-pal"] = {
        "description": "must block pal http",
        "servers": ["pal", "dope-context"],
    }
    inv = profile_policy.resolve_profile(
        cat, "bad-pal", repo_root=REPO_ROOT, check_inventory_baseline=False
    )
    assert "pal" not in inv.selected_servers
    assert "pal" in inv.blocked_servers


def test_planning_audit_uses_pal_stdio_not_pal_http(catalog):
    inv = profile_policy.resolve_profile(
        catalog, "planning-audit", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    assert "pal-stdio" in inv.selected_servers
    assert "pal" not in inv.selected_servers


def test_playwright_absent_from_core_code(catalog):
    inv = profile_policy.resolve_profile(
        catalog, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    assert "playwright-mcp" not in inv.selected_servers
    assert "playwright-mcp" not in inv.visible_tools


def test_github_write_absent_from_normal_profiles(catalog):
    for name in ("core-code", "core-retrieval", "research-docs", "pr-steward"):
        inv = profile_policy.resolve_profile(
            catalog, name, repo_root=REPO_ROOT, check_inventory_baseline=True
        )
        github_tools = inv.visible_tools.get("github-official") or []
        for write in profile_policy.GITHUB_WRITE_TOOLS:
            assert write not in github_tools, f"{name} leaked write tool {write}"
        # Seeded write names must be excluded when present in snapshot
        for write in ("create_issue", "create_pull_request", "merge_pull_request", "push_files"):
            assert write not in github_tools
            assert write in (inv.excluded_tools.get("github-official") or [])


def test_conport_admin_tools_excluded_from_non_admin(catalog):
    inv = profile_policy.resolve_profile(
        catalog, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    conport_vis = inv.visible_tools.get("conport") or []
    for admin in ("fork_instance", "promote", "promote_all"):
        assert admin not in conport_vis
        assert admin in (inv.excluded_tools.get("conport") or [])


def test_missing_domain_executable_blocks(tmp_path, catalog):
    # Empty repo root — no scripts/mcp/domain-read
    ok, msg, tools = profile_policy.validate_repo_domain_read(
        tmp_path, require_tracked=False
    )
    assert ok is False
    assert "missing domain executable" in msg
    assert tools == []

    cat = json.loads(json.dumps(catalog))
    cat["profiles"]["dom"] = {
        "description": "domain only",
        "servers": ["repo-domain-read"],
        "inventory_baseline": {"visible_tool_count": 0},
    }
    inv = profile_policy.resolve_profile(
        cat, "dom", repo_root=tmp_path, check_inventory_baseline=False, require_domain_tracked=False
    )
    assert "repo-domain-read" in inv.blocked_servers
    assert "repo-domain-read" not in inv.selected_servers


def test_untracked_domain_executable_blocks(tmp_path, catalog):
    exe = tmp_path / "scripts" / "mcp" / "domain-read"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    manifest = tmp_path / "mcp" / "domain-read-tools.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "name": "domain_ping",
                        "side_effect": "READ_ONLY_NO_DURABLE_SIDE_EFFECT",
                        "input_schema_digest": "a" * 64,
                        "output_schema_digest": "b" * 64,
                    }
                ]
            }
        )
    )
    # Not a git repo / untracked
    ok, msg, _ = profile_policy.validate_repo_domain_read(tmp_path, require_tracked=True)
    assert ok is False
    assert "tracked" in msg.lower() or "unable to verify" in msg.lower()


def test_symlink_path_escape_blocked(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "evil"
    target.write_text("#!/bin/sh\n")
    root = tmp_path / "repo"
    (root / "scripts" / "mcp").mkdir(parents=True)
    (root / "mcp").mkdir(parents=True)
    link = root / "scripts" / "mcp" / "domain-read"
    link.symlink_to(target)
    (root / "mcp" / "domain-read-tools.json").write_text("{}")
    ok, msg, _ = profile_policy.validate_repo_domain_read(root, require_tracked=False)
    assert ok is False
    assert "symlink" in msg.lower() or "escape" in msg.lower()


def test_malformed_domain_manifest_blocked(tmp_path):
    exe = tmp_path / "scripts" / "mcp" / "domain-read"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\n")
    man = tmp_path / "mcp" / "domain-read-tools.json"
    man.parent.mkdir(parents=True)
    man.write_text("{not-json")
    ok, msg, _ = profile_policy.validate_repo_domain_read(tmp_path, require_tracked=False)
    assert ok is False
    assert "malformed" in msg.lower()


def test_write_unknown_side_effect_tools_blocked(tmp_path):
    exe = tmp_path / "scripts" / "mcp" / "domain-read"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\n")
    man = tmp_path / "mcp" / "domain-read-tools.json"
    man.parent.mkdir(parents=True)
    man.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "name": "domain_write",
                        "side_effect": "WRITE",
                        "input_schema_digest": "a" * 64,
                        "output_schema_digest": "b" * 64,
                    }
                ]
            }
        )
    )
    ok, msg, _ = profile_policy.validate_repo_domain_read(tmp_path, require_tracked=False)
    assert ok is False
    assert "READ_ONLY_NO_DURABLE_SIDE_EFFECT" in msg

    man.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "name": "domain_mystery",
                        "side_effect": "UNKNOWN",
                        "input_schema_digest": "a" * 64,
                        "output_schema_digest": "b" * 64,
                    }
                ]
            }
        )
    )
    ok, msg, _ = profile_policy.validate_repo_domain_read(tmp_path, require_tracked=False)
    assert ok is False


def test_inventory_drift_fails(catalog):
    cat = json.loads(json.dumps(catalog))
    # Force baseline below actual count
    cat["profiles"]["core-code"]["inventory_baseline"] = {
        "visible_tool_count": 0,
        "rationale": "test",
    }
    with pytest.raises(profile_policy.ProfilePolicyError, match="inventory baseline"):
        profile_policy.resolve_profile(
            cat, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
        )


def test_digests_stable(catalog):
    a = profile_policy.resolve_profile(
        catalog, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    b = profile_policy.resolve_profile(
        catalog, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    assert a.profile_digest == b.profile_digest
    assert a.tool_schema_digest == b.tool_schema_digest
    assert len(a.profile_digest) == 64
    assert len(a.tool_schema_digest) == 64


def test_desktop_commander_not_in_normal_profiles(catalog):
    for name in profile_policy.list_profiles(catalog):
        inv = profile_policy.resolve_profile(
            catalog, name, repo_root=REPO_ROOT, check_inventory_baseline=False
        )
        assert "desktop-commander" not in inv.selected_servers


def test_valid_domain_read_accepted(tmp_path):
    exe = tmp_path / "scripts" / "mcp" / "domain-read"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\necho ok\n")
    exe.chmod(0o755)
    man = tmp_path / "mcp" / "domain-read-tools.json"
    man.parent.mkdir(parents=True)
    man.write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "name": "domain_status",
                        "side_effect": "READ_ONLY_NO_DURABLE_SIDE_EFFECT",
                        "input_schema_digest": "c" * 64,
                        "output_schema_digest": "d" * 64,
                        "authority_source": "app-service",
                        "sensitivity_class": "internal",
                        "max_result_bound": 100,
                    }
                ]
            }
        )
    )
    ok, msg, tools = profile_policy.validate_repo_domain_read(
        tmp_path, require_tracked=False
    )
    assert ok is True, msg
    assert tools == ["domain_status"]
