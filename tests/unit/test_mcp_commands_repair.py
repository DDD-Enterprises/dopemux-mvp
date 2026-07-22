"""CLI tests for repair-config and fleet commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

import pytest
from click.testing import CliRunner

from dopemux.commands import mcp_commands


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["dope-memory"]},
        "servers": {
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
                "management_model": "compose-service",
            }
        },
    }


def _git_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True, capture_output=True)
    (path / "README").write_text("x\n")
    subprocess.run(["git", "add", "README"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path, monkeypatch):
    repo = tmp_path / "fixture"
    _git_init(repo)
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "dope-memory": {"type": "sse", "url": "http://localhost:3060/mcp"},
                    "custom": {"type": "http", "url": "http://localhost:1/x"},
                }
            }
        )
        + "\n"
    )
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(mcp_commands, "_catalog_path", lambda: None)
    monkeypatch.setattr(
        mcp_commands,
        "get_repo_root",
        lambda fallback_cwd=False: str(repo),
    )
    return repo


def test_repair_config_requires_flag(fixture_repo):
    runner = CliRunner()
    result = runner.invoke(mcp_commands.mcp, ["repair-config", "--repo", str(fixture_repo)])
    assert result.exit_code != 0
    assert "exactly one" in result.output.lower() or "dry-run" in result.output.lower()


def test_repair_config_rejects_both_flags(fixture_repo):
    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(fixture_repo), "--dry-run", "--apply"],
    )
    assert result.exit_code != 0


def test_repair_config_dry_run_json(fixture_repo):
    runner = CliRunner()
    before = (fixture_repo / ".mcp.json").read_text()
    result = runner.invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(fixture_repo), "--dry-run", "--json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["operation"] == "repair-config"
    assert data["dry_run"] is True
    assert data["status"] in {"PLANNED", "NOOP"}
    assert (fixture_repo / ".mcp.json").read_text() == before


def test_repair_config_apply_json(fixture_repo):
    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(fixture_repo), "--apply", "--json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "APPLIED"
    mcp = json.loads((fixture_repo / ".mcp.json").read_text())
    # http/sse catalog entries are rendered as stdio + `uvx mcp-proxy ...`
    # (Claude Code proxy wrapper), not a raw type:http/sse + url entry.
    dope_memory = mcp["mcpServers"]["dope-memory"]
    assert dope_memory["type"] == "stdio"
    assert "url" not in dope_memory
    assert dope_memory["command"] == "uvx"
    assert dope_memory["args"][:2] == ["mcp-proxy", "--transport"]
    assert mcp["mcpServers"]["custom"]["url"] == "http://localhost:1/x"
    assert (fixture_repo / ".envrc.dopemux-mcp").is_file()


def test_repair_config_preserves_remote_proxy_target_on_re_apply(fixture_repo):
    """A custom remote/credentialed proxy target must survive a second repair.

    Regression test: after the first --apply migrates an entry to the
    stdio+mcp-proxy shape, a user may hand-edit `args[-1]` to point at a
    remote or credentialed conport/dope-memory instead of the catalog's
    localhost default. A later `repair-config --apply` must not silently
    overwrite that back to the catalog target.
    """
    runner = CliRunner()
    first = runner.invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(fixture_repo), "--apply", "--json"],
    )
    assert first.exit_code == 0, first.output

    mcp_json_path = fixture_repo / ".mcp.json"
    mcp = json.loads(mcp_json_path.read_text())
    remote_url = "https://user:secret@remote-dope-memory.example.com/mcp"
    mcp["mcpServers"]["dope-memory"]["args"][-1] = remote_url
    mcp_json_path.write_text(json.dumps(mcp) + "\n")

    second = runner.invoke(
        mcp_commands.mcp,
        ["repair-config", "--repo", str(fixture_repo), "--apply", "--json"],
    )
    assert second.exit_code == 0, second.output
    data = json.loads(second.output)
    assert any(
        p.get("service") == "dope-memory" and "non-localhost" in p.get("reason", "")
        for p in data.get("preserved_entries", [])
    ), data

    mcp_after = json.loads(mcp_json_path.read_text())
    assert mcp_after["mcpServers"]["dope-memory"]["args"][-1] == remote_url


def test_fleet_init_dry_run_json(fixture_repo, monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        [
            "fleet",
            "init",
            "--repo",
            str(fixture_repo),
            "--worktrees",
            str(fixture_repo),
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["operation"] == "fleet-init"
    assert data["dry_run"] is True


def test_fleet_doctor_json(fixture_repo, monkeypatch):
    # Avoid real docker/network in doctor
    from dopemux.mcp import doctor as doctor_mod

    class FakeReport:
        status = "PASS"
        findings = []
        exit_code = 0

        def to_json(self):
            return "{}"

    monkeypatch.setattr(
        doctor_mod,
        "run_mcp_doctor",
        lambda *a, **k: FakeReport(),
    )
    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        [
            "fleet",
            "doctor",
            "--repo",
            str(fixture_repo),
            "--worktrees",
            str(fixture_repo),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["operation"] == "fleet-doctor"
