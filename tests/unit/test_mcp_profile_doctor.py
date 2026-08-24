"""Profile doctor CLI overlay tests (ADR-DMX-MCPPROF-001)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp import fleet_catalog, profile_policy


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def catalog() -> dict:
    return fleet_catalog.load_root_catalog(REPO_ROOT)


def test_doctor_profile_core_code_json(catalog, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(REPO_ROOT)
    )
    result = CliRunner().invoke(
        mcp_commands.mcp_doctor_cmd,
        ["--profile", "core-code", "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "mcp-profile-doctor-1"
    assert payload["profile"] == "core-code"
    assert "playwright-mcp" not in payload["selected_servers"]
    assert payload["invariants"]["pal_http_selected"] is False
    assert payload["invariants"]["github_writes_visible"] is False
    assert payload["visible_tool_count"] > 0
    assert len(payload["profile_digest"]) == 64


def test_doctor_profile_ui_audit_human(catalog, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(REPO_ROOT)
    )
    result = CliRunner().invoke(
        mcp_commands.mcp_doctor_cmd,
        ["--profile", "ui-audit"],
    )
    assert result.exit_code == 0, result.output
    assert "Profile: ui-audit" in result.output
    assert "playwright-mcp" in result.output
    assert "profile_digest:" in result.output


def test_doctor_unknown_profile_fails(catalog, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(REPO_ROOT)
    )
    result = CliRunner().invoke(
        mcp_commands.mcp_doctor_cmd,
        ["--profile", "nope"],
    )
    assert result.exit_code != 0
    assert "unknown profile" in result.output.lower() or "unknown" in result.output.lower()


def test_doctor_rejects_implicit_all(catalog, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(REPO_ROOT)
    )
    result = CliRunner().invoke(
        mcp_commands.mcp_doctor_cmd,
        ["--profile", "all"],
    )
    assert result.exit_code != 0
    assert "forbidden" in result.output.lower() or "all" in result.output.lower()


def test_profile_list_and_show(catalog, monkeypatch):
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(
        mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(REPO_ROOT)
    )
    listed = CliRunner().invoke(mcp_commands.mcp_profile_list_cmd, [])
    assert listed.exit_code == 0, listed.output
    assert "core-code" in listed.output
    assert "core-retrieval" in listed.output

    shown = CliRunner().invoke(
        mcp_commands.mcp_profile_show_cmd, ["core-code", "--json"]
    )
    assert shown.exit_code == 0, shown.output
    data = json.loads(shown.output)
    assert data["profile"] == "core-code"
    assert "serena" in data["selected_servers"]


def test_render_profile_doctor_report_shape(catalog):
    inv = profile_policy.resolve_profile(
        catalog, "core-code", repo_root=REPO_ROOT, check_inventory_baseline=True
    )
    report = profile_policy.render_profile_doctor_report(inv)
    assert report["baseline_ok"] is True
    assert report["github_read_only"] is True
    human = profile_policy.format_profile_doctor_human(inv)
    assert "Selected servers" in human
