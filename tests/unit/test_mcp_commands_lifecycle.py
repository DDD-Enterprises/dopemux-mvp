"""CLI tests for repo-aware mcp start/stop/status."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from dopemux.commands import mcp_commands


def _catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
            },
        },
    }


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "conport": {"type": "sse", "url": "http://localhost:${CONPORT_MCP_PORT}/sse"},
                }
            }
        )
    )
    (repo / ".envrc.dopemux-mcp").write_text(
        f"export DOPEMUX_WORKSPACE_ID={repo}\n"
        f"export DOPEMUX_WORKSPACE_ROOT={repo}\n"
        f"export DOPEMUX_PROJECT_ROOT={repo}\n"
        f"export CONPORT_MCP_PORT=3041\n"
        f"export CONPORT_HTTP_PORT=3040\n"
        f"export CONPORT_INFO_PORT=4040\n"
        f"export DOPEMUX_INSTANCE_ID=abcd\n"
    )
    return repo


def test_cli_start_dry_run_json(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))

    # Avoid real docker
    import dopemux.mcp.docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["start", "--repo", str(repo), "--services", "conport", "--dry-run", "--json"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["operation"] == "start"
    assert payload["dry_run"] is True
    assert payload["schema_version"] == "1.0"
    assert not reg.exists()  # dry-run no registry


def test_cli_status_json(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))

    import dopemux.mcp.docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["status", "--repo", str(repo), "--json"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["operation"] == "status"
    assert "registry" in payload
    assert "services" in payload


def test_cli_up_repo_aliases_start(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reg = tmp_path / "instances.json"
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MVP_ROOT", str(product))

    import dopemux.mcp.docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **kw: di.DockerInspectResult(available=True, containers=[]),
    )

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["up", "--repo", str(repo), "--services", "conport", "--dry-run", "--json"],
    )
    assert result.exit_code in {0, 1, 2}, result.output
    payload = json.loads(result.output)
    assert payload["operation"] == "start"


def test_cli_up_dry_run_without_repo_stays_legacy(monkeypatch):
    """--dry-run/--json alone must not divert bare `mcp up` to the reconciler."""
    called = {"legacy": False, "lifecycle": False}

    def fake_run(cmd, **kwargs):  # noqa: ARG001
        called["legacy"] = True
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_lifecycle(*args, **kwargs):  # noqa: ARG001
        called["lifecycle"] = True
        raise AssertionError("lifecycle should not run without --repo")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)
    monkeypatch.setattr(mcp_commands, "_run_lifecycle_cli", fake_lifecycle)

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["up", "--services", "conport", "--dry-run", "--json"],
    )
    assert called["lifecycle"] is False, result.output
    assert called["legacy"] is True, result.output
    assert result.exit_code == 0, result.output


def test_cli_up_creates_missing_external_network_before_compose(monkeypatch):
    """Removing network initialization must fail before compose reaches a clean host."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):  # noqa: ARG001
        calls.append(list(cmd))
        if cmd == ["docker", "network", "ls", "--format", "{{.Name}}"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)

    result = CliRunner().invoke(
        mcp_commands.mcp,
        ["up", "--services", "conport"],
    )

    assert result.exit_code == 0, result.output
    assert calls[0] == ["docker", "network", "ls", "--format", "{{.Name}}"]
    assert calls[1] == ["docker", "network", "create", "dopemux-network"]
    assert calls[2] == [
        "docker",
        "compose",
        "-f",
        "compose.yml",
        "up",
        "-d",
        "--build",
        "conport",
    ]


def test_cli_down_dry_run_without_repo_stays_legacy(monkeypatch):
    """--dry-run/--json alone must not divert bare `mcp down` to the reconciler."""
    called = {"legacy": False, "lifecycle": False}

    def fake_run(cmd, check=True):  # noqa: ARG001
        called["legacy"] = True
        return SimpleNamespace(returncode=0)

    def fake_lifecycle(*args, **kwargs):  # noqa: ARG001
        called["lifecycle"] = True
        raise AssertionError("lifecycle should not run without --repo")

    monkeypatch.setattr(mcp_commands.subprocess, "run", fake_run)
    monkeypatch.setattr(mcp_commands, "_run_lifecycle_cli", fake_lifecycle)
    monkeypatch.setattr(mcp_commands, "_compose_services", lambda: {"conport"})
    monkeypatch.setattr(mcp_commands, "DEFAULT_MCP_SERVICES", {"conport"})

    runner = CliRunner()
    result = runner.invoke(
        mcp_commands.mcp,
        ["down", "--dry-run", "--json"],
    )
    assert called["lifecycle"] is False, result.output
    assert called["legacy"] is True, result.output
    assert result.exit_code == 0, result.output
